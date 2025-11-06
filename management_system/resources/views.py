from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Slide, Curso, Documento, TipoDocumento, VideoCurso
from employees.models import Empleado, Departamento
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse
from .forms import CursoForm, DocumentoForm, VideoCursoForm, SlideForm
from django.views.decorators.http import require_POST # <--- 1. IMPORT AÑADIDO

@login_required
def ResourcesView(request):
    # USUARIO ES ADMIN?
    is_admin = request.user.groups.filter(name='Administrativo').exists()
    # SLIDES
    slides_activos = Slide.objects.filter(is_active=True)
    # CURSOS
    mis_cursos = Curso.objects.none()
    cursos_disponibles = Curso.objects.none()
    empleado = None
    user_depto_id = None

    # Inicializa ambos formularios como None
    form_curso = CursoForm(prefix='create_curso') 
    form_documento = DocumentoForm(prefix='create_doc')
    form_video = VideoCursoForm(prefix='create_video')
    form_slide = SlideForm(prefix='create_slide')

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

        elif form_type == 'video':
            form_video = VideoCursoForm(request.POST, prefix='create_video')

            if form_video.is_valid():
                video_guardado = form_video.save()
                messages.success(request, f'¡Nuevo contenido "{video_guardado.titulo}" guardado exitosamente! 📹')
                return redirect('resources:resources')
            else:
                messages.error(request, 'Error al guardar el contenido. Revisa los campos.')
                form_with_errors = 'video' # <-- IMPORTANTE
        
        elif form_type == 'slide':  # <--- IMPORTANTE: Lógica para slide
            form_slide = SlideForm(request.POST, request.FILES, prefix='create_slide')
            if form_slide.is_valid():
                form_slide.save()
                messages.success(request, '¡Nuevo slide añadido correctamente!')
                return redirect('resources:resources')
            else:
                messages.error(request, 'Error al añadir el slide. Revisa los campos.')
                form_with_errors = 'slide'
        
        else:
            # Fallback por si no se identifica el form
            messages.error(request, 'Error desconocido al enviar el formulario.')
            form_curso = CursoForm(prefix='create_curso')
            form_documento = DocumentoForm(prefix='create_doc')
            form_video = VideoCursoForm(prefix='create_video') # <-- AÑADE ESTO

    else:
        # Lógica para el GET (cuando se carga la página)
        form_curso = CursoForm(prefix='create_curso')
        form_documento = DocumentoForm(prefix='create_doc')
        form_video = VideoCursoForm(prefix='create_video') # <-- AÑADE ESTO
    # --- FIN: LÓGICA DE FORMULARIOS MODIFICADA ---

    try:
        empleado = request.user.empleado 
        if empleado and empleado.departamento: # <--- AÑADIDO
            user_depto_id = empleado.departamento.id # <--- AÑADIDO: Guardamos el ID
    except (Empleado.DoesNotExist, AttributeError):
        pass

    if empleado:
        # Obtenemos los cursos donde el empleado está inscrito
        mis_cursos = empleado.cursos_inscritos.filter(
            estado=Curso.Estado.ACTIVO 
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
            estado=Curso.Estado.ACTIVO
        ).exclude(inscritos=empleado).distinct().order_by('fecha')

    chunk_size = 3
    mis_cursos_chunks = [mis_cursos[i:i + chunk_size] for i in range(0, len(mis_cursos), chunk_size)]
    cursos_disponibles_chunks = [cursos_disponibles[i:i + chunk_size] for i in range(0, len(cursos_disponibles), chunk_size)]    
    
    # CONSULTA PARA DOCUMENTOS
    if is_admin:
        documentos_dept_query = Q()
    else:
        # Si no es admin, aplicamos la lógica de permisos normal
        documentos_dept_query = Q(es_general=True)
        if empleado and empleado.departamento:
            documentos_dept_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)

    # 1. CREA LA LISTA DE DOCUMENTOS (Políticas, Manuales, etc.)
    documentos_generales_list = Documento.objects.filter(
        documentos_dept_query, 
        estado='activo',
        tipo_documento__nombre__in=['Manual', 'Política', 'Guía', 'Anexo', 'Documento de interés']
    ).distinct().order_by('nombre')
    
    # 2. CREA LA LISTA DE FORMATOS (Formatos, Plantillas)
    formatos_list = Documento.objects.filter(
        documentos_dept_query, 
        estado='activo',
        tipo_documento__nombre__in=['Formato', 'Plantilla', 'Formato de interés']
    ).distinct().order_by('nombre')

    # 3. CREA LA CONSULTA DE PERMISOS PARA VIDEOS
    if is_admin:
        video_permission_query = Q() # Admin ve todo
    else:
        # Un video es visible si:
        # 1. No tiene curso (es general) O
        # 2. El curso es general O
        # 3. El curso es para el departamento del empleado
        video_permission_query = Q(curso=None) | Q(curso__es_general=True)
        if empleado and empleado.departamento:
            video_permission_query.add(Q(curso__departamentos_destinados=empleado.departamento), Q.OR)

    # 4. CREA LA LISTA DE VIDEOS
    videos_list = VideoCurso.objects.filter(
        video_permission_query, # Aplicamos los permisos
        estado='activo'         # Solo mostramos videos activos
    ).distinct().order_by('-fecha_grabacion') # Orden más reciente primero

    # 3. PAGINA AMBAS LISTAS
    paginator_docs = Paginator(documentos_generales_list, 4)
    paginator_formatos = Paginator(formatos_list, 4)
    paginator_videos = Paginator(videos_list, 4) # <--- AÑADIDO
    
    documentos_page_1 = paginator_docs.get_page(1)
    formatos_page_1 = paginator_formatos.get_page(1)
    videos_page_1 = paginator_videos.get_page(1) # <--- AÑADIDO

    todos_los_cursos_list = Curso.objects.all().order_by('titulo')
    todos_los_documentos_list = Documento.objects.filter(documentos_dept_query).distinct().order_by('nombre')
    todos_los_videos_list = VideoCurso.objects.filter(video_permission_query).distinct().order_by('titulo') # <-- AÑADE ESTO
    all_departamentos = Departamento.objects.all().order_by('nombre')

    tipos_para_documentos = TipoDocumento.objects.filter(
        nombre__in=['Manual', 'Política', 'Guía', 'Anexo', 'Documento de interés']
    ).order_by('nombre')
    
    # Lista de tipos para la sección "Formatos"
    tipos_para_formatos = TipoDocumento.objects.filter(
        nombre__in=['Formato', 'Plantilla', 'Formato de interés']
    ).order_by('nombre')

    context = {
        'form_curso': form_curso,
        'form_documento': form_documento,
        'form_video': form_video,
        'form_slide': form_slide,
        'slides': slides_activos,
        'mis_cursos_chunks': mis_cursos_chunks,                  # <-- Lista 1 (Cursos registrados)
        'cursos_disponibles_chunks': cursos_disponibles_chunks,  # <-- Lista 2 (Cursos disponibles) 
        'todos_los_cursos': todos_los_cursos_list,               # <-- Lista 3 (Todos los cursos)
        'todos_los_documentos': todos_los_documentos_list, # <-- Actualizado        
        'todos_los_videos': todos_los_videos_list, # <-- AÑADE ESTO
        'documentos_generales': documentos_page_1,
        'formatos': formatos_page_1,  
        'is_admin': is_admin,
        'form_with_errors': form_with_errors,

        'all_departamentos': all_departamentos,
        'tipos_para_documentos': tipos_para_documentos,
        'tipos_para_formatos': tipos_para_formatos,
        'user_depto_id': user_depto_id,

        'videos_videoteca': videos_page_1,
    }
    return render(request, 'resources.html', context)

@login_required 
def BuscarDocumentosView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '') # El término de búsqueda del input
    depto_id = request.GET.get('departamento', '')
    tipo_id = request.GET.get('tipo', '')
    is_admin = request.user.groups.filter(name='Administrativo').exists()

    lookup = (
        Q(nombre__icontains=query) |
        Q(codigo_documento__icontains=query) |
        Q(palabras_clave__icontains=query)
    )
    
    empleado = None
    try:
        empleado = request.user.empleado
    except (Empleado.DoesNotExist, AttributeError):
        pass

    # El "mundo" de documentos que este usuario tiene permitido ver
    permission_query = Q(es_general=True)
    if empleado and empleado.departamento:
        permission_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)

    if depto_id:
        # Si se seleccionó un depto específico ("1", "2", etc.)
        filter_query = Q(departamentos_destinados__id=depto_id)
    else:
        filter_query = Q(es_general=True)    
        if empleado and empleado.departamento:
            filter_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)
        # --- FIN MODIFICADO ---

    tipo_query_base = Q(tipo_documento__nombre__in=['Manual', 'Política', 'Guía', 'Anexo', 'Documento de interés']) # <--- MODIFICADO
    
    documentos_list = Documento.objects.filter(
        permission_query, # <-- 1. APLICAR PERMISOS PRIMERO
        filter_query,
        lookup, 
        tipo_query_base, # <--- MODIFICADO
        estado='activo'
    )

    if tipo_id:
        documentos_list = documentos_list.filter(tipo_documento__id=tipo_id)

    documentos_list = documentos_list.distinct().order_by('nombre') # <--- MODIFICADO (movido después del filtro de tipo)

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

@login_required
def BuscarFormatosView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '') # El término de búsqueda del input
    depto_id = request.GET.get('departamento', '')
    tipo_id = request.GET.get('tipo', '')

    is_admin = request.user.groups.filter(name='Administrativo').exists()

    lookup = (
        Q(nombre__icontains=query) |
        Q(codigo_documento__icontains=query) |
        Q(palabras_clave__icontains=query)
    )

    empleado = None
    try:
        empleado = request.user.empleado
    except (Empleado.DoesNotExist, AttributeError):
        pass

    # El "mundo" de documentos que este usuario tiene permitido ver
    permission_query = Q(es_general=True)
    if empleado and empleado.departamento:
        permission_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)
    
    if depto_id:
        # REQ 1: Si se selecciona un depto, mostrar SOLO de ese depto.
        filter_query = Q(departamentos_destinados__id=depto_id)    
    else:
        # REQ 2: Si se selecciona "Todos" (depto_id=''), mostrar SOLO 'es_general=True'.
        filter_query = Q(es_general=True)    
        # --- FIN MODIFICADO ---

    tipo_query_base = Q(tipo_documento__nombre__in=['Formato', 'Plantilla', ''])

    documentos_list = Documento.objects.filter(
        permission_query, # <-- 1. APLICAR PERMISOS PRIMERO
        filter_query,
        lookup, 
        tipo_query_base,
        estado='activo'
    )
    if tipo_id:
        documentos_list = documentos_list.filter(tipo_documento__id=tipo_id)

    documentos_list = documentos_list.distinct().order_by('nombre') # <--- MODIFICADO (movido después del filtro de tipo)
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

@login_required
def InscribirCursoView(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    
    try:
        empleado = request.user.empleado
    except Empleado.DoesNotExist:
        messages.error(request, "No tienes un perfil de empleado asociado para inscribirte.")
        return redirect('resources:resources')

    # Verificar si ya está inscrito
    if curso.inscritos.filter(id=empleado.id).exists():
        messages.info(request, f"Ya estás inscrito en el curso '{curso.titulo}'.")
    elif curso.modalidad == Curso.Modalidad.AUTOINSCRIPCION:
        # Realizar la inscripción
        curso.inscritos.add(empleado)
        messages.success(request, f"¡Te has inscrito correctamente al curso '{curso.titulo}'! 🎉")
    else:
        messages.error(request, "Este curso requiere solicitud de inscripción.")

    # Redirigir de vuelta a la página de recursos (o donde estabas)
    return redirect('resources:resources')

@login_required
def BuscarVideosView(request):
    """
    Maneja las solicitudes AJAX para buscar y paginar la videoteca.
    """
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '') # El término de búsqueda
    depto_id = request.GET.get('departamento', '')
    # No hay 'tipo_id' para videos

    is_admin = request.user.groups.filter(name='Administrativo').exists()

    # Búsqueda por Título, Ponente, o Título del Curso
    lookup = (
        Q(titulo__icontains=query) |
        Q(ponente__icontains=query) |
        Q(curso__titulo__icontains=query) # Búsqueda en el curso relacionado
    )
    
    empleado = None
    try:
        empleado = request.user.empleado
    except (Empleado.DoesNotExist, AttributeError):
        pass

    # 1. PERMISOS: El "mundo" de videos que este usuario puede ver
    if is_admin:
        permission_query = Q() # Admin ve todo
    else:
        permission_query = Q(es_general=True)
        if empleado and empleado.departamento:
            permission_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)
    
    # 2. FILTRO: El filtro de departamento seleccionado
    if depto_id:
        # Si se seleccionó un depto específico ("1", "2", etc.)
        filter_query = Q(departamentos_destinados__id=depto_id)
    else:
        # "Todos los Departamentos"
        # Muestra todo lo que está en el scope de permisos
        filter_query = permission_query 
    
    videos_list = VideoCurso.objects.filter(
        permission_query, # Permisos base (si no es admin)
        filter_query,   # Filtro del dropdown
        lookup,         # Filtro de búsqueda
        estado='activo'
    ).distinct().order_by('-fecha_grabacion')

    paginator = Paginator(videos_list, 4) # Paginar por 4
    page_obj = paginator.get_page(page_number)

    html = render_to_string(
        template_name='_videos_partial.html', # <-- Usar el partial de video
        context={
            'videos': page_obj, # <-- Pasar 'videos'
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

@user_passes_test(is_admin_check)
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

@user_passes_test(is_admin_check)
def VideoEditView(request, video_id):
    """
    Maneja el GET (cargar formulario parcial) y POST (actualizar)
    para el modal de edición de videos/contenido.
    """
    video = get_object_or_404(VideoCurso, id=video_id)
    
    if request.method == 'POST':
        # El usuario está enviando el formulario actualizado
        form = VideoCursoForm(request.POST, request.FILES, instance=video, prefix="edit-video")
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Contenido "{video.titulo}" actualizado con éxito.')
            return redirect('resources:resources')
        else:
            # Si el formulario no es válido, re-renderizamos el parcial con errores
            messages.error(request, 'Error al actualizar el contenido. Revisa los campos.')
            pass # Continúa para renderizar el form con errores abajo

    else:
        # El usuario está pidiendo el formulario por primera vez (AJAX/Fetch)
        form = VideoCursoForm(instance=video, prefix="edit-video")
    
    # Para GET o POST fallido, renderizamos el formulario parcial
    return render(request, '_video_edit_form.html', {
        'form_video': form, # <-- Nombre de variable 'form_video'
        'video': video
    })

@user_passes_test(is_admin_check)
def SlideEditView(request, slide_id):
    slide = get_object_or_404(Slide, id=slide_id)
    
    if request.method == 'POST':
        form = SlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            form.save()
            messages.success(request, f'Slide "{slide.title}" actualizado correctamente. 👍')
            return redirect('resources:resources') # Redirige tras guardar
        else:
            # Si hay error en POST, podrías devolver el parcial con errores
            # Para simplificar, por ahora redirigimos con mensaje de error
             messages.error(request, 'Error al actualizar el slide. Verifica los datos.')
             return redirect('resources:resources')

    else:
        # GET request: Devolver SOLO el formulario parcial
        form = SlideForm(instance=slide)
        return render(request, '_slide_edit_form.html', { # <--- USAR LA PLANTILLA PARCIAL
            'form': form
        })