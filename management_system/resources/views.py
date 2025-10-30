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
from django.views.decorators.http import require_POST # <--- 1. IMPORT AÑADIDO

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
    form_curso = CursoForm(prefix='create_curso') 
    form_documento = DocumentoForm(prefix='create_doc')

    form_with_errors = None

    # Lógica para el POST (cuando se envía el modal)
    if request.method == 'POST':
        # Identificamos qué formulario se envió
        form_type = request.POST.get('form_type')

        if form_type == 'curso':
            form_curso = CursoForm(request.POST, request.FILES, prefix='create_curso')         

            if form_curso.is_valid():
                curso_guardado = form_curso.save() # Guardamos la instancia
                messages.success(request, f'¡Nuevo curso "{curso_guardado.titulo}" guardado exitosamente! 👍')                
                return redirect('resources:resources') 
            else:
                messages.error(request, 'Error al guardar el curso. Revisa los campos.')
                form_with_errors = 'curso'
        
        elif form_type == 'documento':
            form_documento = DocumentoForm(request.POST, request.FILES, prefix='create_doc')        
                
            if form_documento.is_valid():
                doc_guardado = form_documento.save() # Guardamos la instancia
                # 2. Mensaje de éxito dinámico
                messages.success(request, f'¡Nuevo documento "{doc_guardado.nombre}" guardado exitosamente! 📄')
                return redirect('resources:resources')
            else:
                messages.error(request, 'Error al guardar el documento. Revisa los campos.')
                form_with_errors = 'documento'
        else:
            # Fallback por si no se identifica el form
            messages.error(request, 'Error desconocido al enviar el formulario.')
            form_curso = CursoForm(prefix='create_curso')
            form_documento = DocumentoForm(prefix='create_doc')

    else:
        # Lógica para el GET (cuando se carga la página)
        form_curso = CursoForm(prefix='create_curso')
        form_documento = DocumentoForm(prefix='create_doc')
    # --- FIN: LÓGICA DE FORMULARIOS MODIFICADA ---

    try:
        empleado = request.user.empleado 
    except (Empleado.DoesNotExist, AttributeError):
        pass

    if empleado:
        # Obtenemos los cursos donde el empleado está inscrito
        mis_cursos = empleado.cursos_inscritos.filter(
            estado=Curso.Estado.ACTIVO  # <-- CAMBIO AQUÍ
        ).order_by('fecha')
    # Empleado con departamento, ve solo sus cursos
    if empleado and empleado.departamento:
        query_disponibles = Q(es_general=True) | Q(departamentos_destinados=empleado.departamento)
        cursos_disponibles = Curso.objects.filter(
            query_disponibles, 
            estado=Curso.Estado.ACTIVO
        ).exclude(inscritos=empleado).distinct().order_by('fecha')
    else:
        # Empleado sin departamento, solo ve generales
        cursos_disponibles = Curso.objects.filter(
            es_general=True,
            estado=Curso.Estado.ACTIVO  # <-- CAMBIO AQUÍ
        ).exclude(inscritos=empleado).distinct().order_by('fecha')

    chunk_size = 3
    mis_cursos_chunks = [mis_cursos[i:i + chunk_size] for i in range(0, len(mis_cursos), chunk_size)]
    cursos_disponibles_chunks = [cursos_disponibles[i:i + chunk_size] for i in range(0, len(cursos_disponibles), chunk_size)]    
    
    documentos_dept_query = Q(es_general=True)
    if empleado and empleado.departamento:
        documentos_dept_query = Q(es_general=True) | Q(departamentos_destinados=empleado.departamento)

    # 1. CREA LA LISTA DE DOCUMENTOS (Políticas, Manuales, etc.)
    #    Ajusta los nombres en __in=[...] según tu base de datos
    documentos_generales_list = Documento.objects.filter(
        documentos_dept_query, 
        estado='activo',
        tipo_documento__nombre__in=['Manual', 'Política', 'Guía', 'Anexo', 'Documento de interés']
    ).distinct().order_by('nombre')
    
    # 2. CREA LA LISTA DE FORMATOS (Formatos, Plantillas)
    #    Ajusta los nombres en __in=[...] según tu base de datos
    formatos_list = Documento.objects.filter(
        documentos_dept_query, 
        estado='activo',
        tipo_documento__nombre__in=['Formato', 'Plantilla', 'Formato de interés']
    ).distinct().order_by('nombre')

    # 3. PAGINA AMBAS LISTAS
    paginator_docs = Paginator(documentos_generales_list, 4)
    paginator_formatos = Paginator(formatos_list, 4)
    
    documentos_page_1 = paginator_docs.get_page(1)
    formatos_page_1 = paginator_formatos.get_page(1)

    todos_los_cursos_list = Curso.objects.all().order_by('titulo')

    context = {
        'form_curso': form_curso,
        'form_documento': form_documento,
        'slides': slides_activos,
        'mis_cursos_chunks': mis_cursos_chunks,                  # <-- Lista 1 (Cursos registrados)
        'cursos_disponibles_chunks': cursos_disponibles_chunks,  # <-- Lista 2 (Cursos disponibles) 
        'todos_los_cursos': todos_los_cursos_list,               # <-- Lista 3 (Todos los cursos)
        'todos_los_documentos': Documento.objects.filter(documentos_dept_query).distinct().order_by('nombre'),        
        'documentos_generales': documentos_page_1, # Reemplaza a 'documentos'
        'formatos': formatos_page_1,  
        'is_admin': is_admin,                                    # <-- Comprobación si es del grupo Administrador
        'form_with_errors': form_with_errors
    }
    return render(request, 'resources.html', context)

@login_required 
def BuscarDocumentosView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '') # El término de búsqueda del input

    is_admin = request.user.groups.filter(name='Administrativo').exists()

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

    tipo_query = Q(tipo_documento__nombre__in=['Manual', 'Política', 'Guía', 'Anexo', 'Documento de interés'])
    documentos_list = Documento.objects.filter(
        lookup, 
        documentos_dept_query, 
        tipo_query,
        estado='activo'
    ).distinct().order_by('nombre')

    paginator = Paginator(documentos_list, 4)
    page_obj = paginator.get_page(page_number)

    html = render_to_string(
        template_name='_documentos_partial.html',
        context={
            'documentos': page_obj,
            'is_admin': is_admin
        }    
    )

    return JsonResponse({
        'html': html,
        'has_next': page_obj.has_next()
    })

@login_required # <--- ¡AÑADE ESTA LÍNEA!   
def BuscarFormatosView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '') # El término de búsqueda del input

    is_admin = request.user.groups.filter(name='Administrativo').exists()
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

    tipo_query = Q(tipo_documento__nombre__in=['Formato', 'Plantilla', 'Formato de interés'])    

    documentos_list = Documento.objects.filter(
        lookup, 
        documentos_dept_query, 
        tipo_query,
        estado='activo'
    ).distinct().order_by('nombre')

    paginator = Paginator(documentos_list, 4)
    page_obj = paginator.get_page(page_number)

    html = render_to_string(
        template_name='_documentos_partial.html',
        context={
            'documentos': page_obj,
            'is_admin': is_admin
        }    
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
            messages.success(request, f'¡Curso "{curso.titulo}" actualizado exitosamente! 🚀')            # Redirigimos a la página principal del repositorio
            return redirect('resources:resources')
        else:
            # Si el form no es válido, se lo devolvemos al JS con los errores
            messages.warning(request, 'Hubo un error al actualizar. Revisa los campos.')
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

@user_passes_test(is_admin_check)
def edit_documento(request, documento_id):
    """
    Maneja el GET (cargar formulario parcial) y POST (actualizar)
    para el modal de edición de documentos.
    """
    documento = get_object_or_404(Documento, id=documento_id)
    
    if request.method == 'POST':
        # El usuario está enviando el formulario actualizado
        form = DocumentoForm(request.POST, request.FILES, instance=documento, prefix="edit-doc")
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Documento "{documento.nombre}" actualizado con éxito.')
            return redirect('resources:resources')
        else:
            # Si el formulario no es válido, re-renderizamos el parcial con errores
            messages.error(request, 'Error al actualizar el documento. Revisa los campos.')
            pass # Continúa para renderizar el form con errores abajo

    else:
        # El usuario está pidiendo el formulario por primera vez (AJAX/Fetch)
        form = DocumentoForm(instance=documento, prefix="edit-doc")
    
    # Para GET o POST fallido, renderizamos el formulario parcial
    return render(request, '_edit_documento_form.html', {
        'form_documento': form,
        'documento': documento
    })
