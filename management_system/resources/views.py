from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Slide, Curso, Documento, TipoDocumento, VideoCurso, InscripcionCurso
from employees.models import Empleado, Departamento
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse
from .forms import CursoForm, DocumentoForm, VideoCursoForm, SlideForm

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
        if empleado and empleado.departamento:
            user_depto_id = empleado.departamento.id
    except (Empleado.DoesNotExist, AttributeError):
        pass

    if empleado:
        mis_cursos = empleado.cursos_inscritos.filter(
            estado=Curso.Estado.ACTIVO 
        ).order_by('fecha')

    if empleado:
        # EMPLEADO NORMAL: Ve solo los de su depto o generales.
        if empleado.departamento:
            # Empleado CON departamento
            query_disponibles = Q(es_general=True) | Q(departamentos_destinados=empleado.departamento)
        else:
            # Empleado SIN departamento
            query_disponibles = Q(es_general=True)
        
        cursos_disponibles = Curso.objects.filter(
            query_disponibles, 
            estado=Curso.Estado.ACTIVO
        ).exclude(inscritos=empleado).distinct().order_by('fecha')
        
    else:
        # Usuario SIN perfil de empleado
        # (Este caso ya casi no debería pasar si todos tienen perfil)
        cursos_disponibles = Curso.objects.filter(
            es_general=True,
            estado=Curso.Estado.ACTIVO
        ).distinct().order_by('fecha')

    chunk_size = 3
    mis_cursos_chunks = [mis_cursos[i:i + chunk_size] for i in range(0, len(mis_cursos), chunk_size)]
    cursos_disponibles_chunks = [cursos_disponibles[i:i + chunk_size] for i in range(0, len(cursos_disponibles), chunk_size)]    

    if is_admin:
        documentos_dept_query = Q()
    else:
        documentos_dept_query = Q(es_general=True)
        if empleado and empleado.departamento:
            documentos_dept_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)

    documentos_generales_list = Documento.objects.filter(
        documentos_dept_query, 
        estado='activo',
        tipo_documento__nombre__in=['Manual', 'Política', 'Guía', 'Anexo', 'Documento de interés']
    ).distinct().order_by('nombre')
    
    formatos_list = Documento.objects.filter(
        documentos_dept_query, 
        estado='activo',
        tipo_documento__nombre__in=['Formato', 'Plantilla', 'Formato de interés']
    ).distinct().order_by('nombre')

    if is_admin:
        video_permission_query = Q() # Admin ve todo
    else:
        video_permission_query = Q(curso=None) | Q(curso__es_general=True)
        if empleado and empleado.departamento:
            video_permission_query.add(Q(curso__departamentos_destinados=empleado.departamento), Q.OR)

    videos_list = VideoCurso.objects.filter(
        video_permission_query, # Aplicamos los permisos
        estado='activo'         # Solo mostramos videos activos
    ).distinct().order_by('-fecha_grabacion') # Orden más reciente primero

    paginator_docs = Paginator(documentos_generales_list, 4)
    paginator_formatos = Paginator(formatos_list, 4)
    paginator_videos = Paginator(videos_list, 4)
    
    documentos_page_1 = paginator_docs.get_page(1)
    formatos_page_1 = paginator_formatos.get_page(1)
    videos_page_1 = paginator_videos.get_page(1)

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
    query = request.GET.get('q', '')
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

    permission_query = Q(es_general=True)
    if empleado and empleado.departamento:
        permission_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)

    if depto_id:
        filter_query = Q(departamentos_destinados__id=depto_id)
    else:
        filter_query = Q(es_general=True)    
        if empleado and empleado.departamento:
            filter_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)

    tipo_query_base = Q(tipo_documento__nombre__in=['Manual', 'Política', 'Guía', 'Anexo', 'Documento de interés'])
    
    documentos_list = Documento.objects.filter(
        permission_query,
        filter_query,
        lookup, 
        tipo_query_base,
        estado='activo'
    )

    if tipo_id:
        documentos_list = documentos_list.filter(tipo_documento__id=tipo_id)

    documentos_list = documentos_list.distinct().order_by('nombre')

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
    query = request.GET.get('q', '')
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

    permission_query = Q(es_general=True)
    if empleado and empleado.departamento:
        permission_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)
    
    if depto_id:
        filter_query = Q(departamentos_destinados__id=depto_id)    
    else:
        filter_query = Q(es_general=True)    

    tipo_query_base = Q(tipo_documento__nombre__in=['Formato', 'Plantilla', ''])

    documentos_list = Documento.objects.filter(
        permission_query,
        filter_query,
        lookup, 
        tipo_query_base,
        estado='activo'
    )
    if tipo_id:
        documentos_list = documentos_list.filter(tipo_documento__id=tipo_id)

    documentos_list = documentos_list.distinct().order_by('nombre')
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

    # 1. Buscar el registro de historial existente
    inscripcion_existente = InscripcionCurso.objects.filter(
        curso=curso, 
        empleado=empleado
    ).first()
    
    if inscripcion_existente:
        
        # A. Bloquear si el registro NO está dado de baja (Es un estado activo: INSCRITO, APROBADO, etc.)
        if inscripcion_existente.estado != InscripcionCurso.EstadoInscripcion.DADO_DE_BAJA:
            messages.info(request, f"Ya tienes un registro activo para el curso '{curso.titulo}'. Estado: {inscripcion_existente.get_estado_display()}")
            return redirect('resources:resources') # Bloquea aquí.

        # B. Si el registro SÍ está 'Dado de Baja', lo eliminamos para crear un registro limpio.
        else: 
            # 1. Eliminar el registro de historial (InscripcionCurso)
            inscripcion_existente.delete()
            
            # 2. Eliminar la relación M2M simple (inscritos)
            if empleado in curso.inscritos.all():
                curso.inscritos.remove(empleado)
                
            # 3. La ejecución continúa a la creación de la nueva inscripción.
    
    # --- 3. CREACIÓN DE LA INSCRIPCIÓN (Se ejecuta si no había registro activo o fue eliminado) ---
    
    # Comprobar si la modalidad permite la inscripción (esto ahora maneja el caso inicial Y el caso de reinscripción)
    if curso.modalidad == Curso.Modalidad.AUTOINSCRIPCION: 
        
        # 1. Crear el objeto de Historial Detallado (InscripcionCurso)
        InscripcionCurso.objects.create(
            curso=curso,
            empleado=empleado,
            # Se asume que la inscripción significa finalización (usando curso.fecha)
            fecha_finalizacion= curso.fecha,
            estado=InscripcionCurso.EstadoInscripcion.INSCRITO 
        )
        
        # 2. Agregar a la relación M2M simple (inscritos)
        curso.inscritos.add(empleado)
        
        messages.success(request, f"¡Te has inscrito correctamente al curso '{curso.titulo}'! 🎉")
        
    elif curso.modalidad != Curso.Modalidad.AUTOINSCRIPCION:
        messages.error(request, "Este curso requiere solicitud de inscripción.")

    return redirect('resources:resources')

@login_required
def BuscarVideosView(request):

    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '')
    depto_id = request.GET.get('departamento', '')

    is_admin = request.user.groups.filter(name='Administrativo').exists()

    lookup = (
        Q(titulo__icontains=query) |
        Q(ponente__icontains=query) |
        Q(curso__titulo__icontains=query)
    )
    
    empleado = None
    try:
        empleado = request.user.empleado
    except (Empleado.DoesNotExist, AttributeError):
        pass

    if is_admin:
        permission_query = Q()
    else:
        permission_query = Q(es_general=True)
        if empleado and empleado.departamento:
            permission_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)
    
    if depto_id:
        filter_query = Q(departamentos_destinados__id=depto_id)
    else:
        filter_query = permission_query 
    
    videos_list = VideoCurso.objects.filter(
        permission_query,
        filter_query,
        lookup,
        estado='activo'
    ).distinct().order_by('-fecha_grabacion')

    paginator = Paginator(videos_list, 4)
    page_obj = paginator.get_page(page_number)

    html = render_to_string(
        template_name='_videos_partial.html',
        context={
            'videos': page_obj,
            'is_admin': is_admin
        }    
    )

    return JsonResponse({
        'html': html,
        'has_next': page_obj.has_next()
    })

def is_admin_check(user):
    return user.is_authenticated and user.groups.filter(name='Administrativo').exists()

@user_passes_test(is_admin_check)
def CursoEditView(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    if request.method == 'POST':
        form = CursoForm(request.POST, request.FILES, instance=curso, prefix='edit')
        
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Curso "{curso.titulo}" actualizado exitosamente! 🚀')
            return redirect('resources:resources')
        else:
            messages.warning(request, 'Hubo un error al actualizar. Revisa los campos.')
            pass 
            
    else:
        form = CursoForm(instance=curso, prefix='edit')

    return render(request, '_curso_edit_form.html', {
        'form': form
    })

@user_passes_test(is_admin_check)
def edit_documento(request, documento_id):

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

             messages.error(request, 'Error al actualizar el slide. Verifica los datos.')
             return redirect('resources:resources')

    else:
        # GET request: Devolver SOLO el formulario parcial
        form = SlideForm(instance=slide)
        return render(request, '_slide_edit_form.html', { # <--- USAR LA PLANTILLA PARCIAL
            'form': form
        })