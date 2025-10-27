from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Slide, Curso, Documento, TipoDocumento
from employees.models import Empleado, Departamento
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse
from .forms import CursoForm, DocumentoForm
from django.contrib.auth.models import Group

@login_required
def ResourcesView(request):
    # USUARIO ES ADMIN?
    is_admin = request.user.groups.filter(name='Administrativo').exists()

    # SLIDES
    slides_activos = Slide.objects.filter(is_active=True)
    # CURSOS
    mis_cursos = Curso.objects.none() # Queryset vacío por si no hay empleado
    cursos_disponibles = Curso.objects.none()
    empleado = None

    # Inicializa ambos formularios como None
    form_curso = CursoForm()
    form_documento = DocumentoForm()

    # Lógica para el POST (cuando se envía el modal)
    if request.method == 'POST':
        # Identificamos qué formulario se envió
        form_type = request.POST.get('form_type')

        if form_type == 'curso':
            form_curso = CursoForm(request.POST, request.FILES)
            if form_curso.is_valid():
                form_curso.save()
                messages.success(request, '¡Nuevo curso guardado exitosamente! 👍')
                return redirect(request.path_info) 
            else:
                messages.error(request, 'Error al guardar el curso. Revisa los campos.')
        
        elif form_type == 'documento':
            form_documento = DocumentoForm(request.POST, request.FILES)
            if form_documento.is_valid():
                form_documento.save()
                messages.success(request, '¡Nuevo documento guardado exitosamente! 📄')
                return redirect(request.path_info)
            else:
                messages.error(request, 'Error al guardar el documento. Revisa los campos.')
        
        else:
            # Fallback por si no se identifica el form
            messages.error(request, 'Error desconocido al enviar el formulario.')
            form_curso = CursoForm()
            form_documento = DocumentoForm()

    else:
        # Lógica para el GET (cuando se carga la página)
        form_curso = CursoForm() # Crea un formulario de curso vacío
        form_documento = DocumentoForm() # Crea un formulario de documento vacío
    # --- FIN: LÓGICA DE FORMULARIOS MODIFICADA ---

    try:
        empleado = request.user.empleado 
    except (Empleado.DoesNotExist, AttributeError):
        pass

    if empleado:
        # Obtenemos los cursos donde el empleado está inscrito
        mis_cursos = empleado.cursos_inscritos.all().order_by('fecha')

    # Empleado con departamento, ve solo sus cursos
    if empleado and empleado.departamento:
        query_disponibles = Q(es_general=True) | Q(departamentos_destinados=empleado.departamento)
        cursos_disponibles = Curso.objects.filter(query_disponibles)\
            .exclude(inscritos=empleado)\
            .distinct()\
            .order_by('fecha')
    else:
        # Empleado sin departamento, solo ve generales
        cursos_disponibles = Curso.objects.filter(es_general=True)\
            .exclude(inscritos=empleado)\
            .distinct()\
            .order_by('fecha')

    chunk_size = 3
    mis_cursos_chunks = [mis_cursos[i:i + chunk_size] for i in range(0, len(mis_cursos), chunk_size)]
    cursos_disponibles_chunks = [cursos_disponibles[i:i + chunk_size] for i in range(0, len(cursos_disponibles), chunk_size)]    
    
    documentos_dept_query = Q(es_general=True)
    if empleado and empleado.departamento:
        documentos_dept_query = Q(es_general=True) | Q(departamentos_destinados=empleado.departamento)

    documentos_list = Documento.objects.filter(
        documentos_dept_query, 
        estado='activo'
    ).distinct().order_by('nombre')
    
    paginator = Paginator(documentos_list, 4)
    documentos_page_1 = paginator.get_page(1)

    todos_los_cursos_list = Curso.objects.all().order_by('titulo')

    context = {
        'form_curso': form_curso,         # <--- Variable actualizada
        'form_documento': form_documento,
        'slides': slides_activos,
        'mis_cursos_chunks': mis_cursos_chunks,                  # <-- Lista 1 (Cursos registrados)
        'cursos_disponibles_chunks': cursos_disponibles_chunks,  # <-- Lista 2 (Cursos disponibles) 
        'todos_los_cursos': todos_los_cursos_list,               # <-- Lista 3 (Todos los cursos)
        'documentos': documentos_page_1,   
        'is_admin': is_admin,                                    # <-- Comprobación si es del grupo Administrador
    }
    return render(request, 'resources.html', context)

@login_required 
def BuscarDocumentosView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '') # El término de búsqueda del input

    empleado = None
    try:
        empleado = request.user.empleado 
    except (Empleado.DoesNotExist, AttributeError):
        pass

    lookup = (
        Q(nombre__icontains=query) |
        Q(codigo_documento__icontains=query) |
        Q(palabras_clave__icontains=query)
    )
    
    documentos_dept_query = Q(es_general=True)
    if empleado and empleado.departamento:
        documentos_dept_query = Q(es_general=True) | Q(departamentos_destinados=empleado.departamento)

    documentos_list = Documento.objects.filter(
        lookup, 
        documentos_dept_query, 
        estado='activo'
    ).distinct().order_by('nombre')

    paginator = Paginator(documentos_list, 4)
    page_obj = paginator.get_page(page_number)

    html = render_to_string(
        template_name='_documentos_partial.html',
        context={'documentos': page_obj}
    )

    return JsonResponse({
        'html': html,
        'has_next': page_obj.has_next()
    })


# Función para verificar si es admin
def is_admin_check(user):
    return user.is_authenticated and user.groups.filter(name='Administrativo').exists()

@user_passes_test(is_admin_check) # Protege la vista para que solo admins entren
def CursoEditView(request, curso_id):
    # Obtenemos el curso que se quiere editar
    curso = get_object_or_404(Curso, id=curso_id)

    if request.method == 'POST':
        # Si el método es POST, estamos guardando cambios
        # Usamos 'instance=curso' para que el form sepa que estamos editando
        form = CursoForm(request.POST, request.FILES, instance=curso, prefix='edit')
        
        if form.is_valid():
            form.save()
            messages.success(request, '¡Curso actualizado exitosamente! 🚀')
            # Redirigimos a la página principal del repositorio
            return redirect('resources:resources')
        else:
            # Si el form no es válido, se lo devolvemos al JS con los errores
            messages.error(request, 'Hubo un error al actualizar. Revisa los campos.')
            # (El JS recibirá este HTML y lo mostrará en el modal)
            pass 
            
    else:
        # Si el método es GET, solo estamos pidiendo el formulario
        # Usamos 'instance=curso' para pre-llenar los datos
        # Usamos 'prefix' para que los IDs de los campos (ej: "id_edit-titulo")
        # no choquen con los del modal de "Crear Curso" (ej: "id_titulo")
        form = CursoForm(instance=curso, prefix='edit')

    # Renderizamos solo el formulario en una plantilla parcial
    return render(request, '_curso_edit_form.html', {
        'form': form
    })