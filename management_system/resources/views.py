from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Slide, Curso, Documento, TipoDocumento, VideoCurso, InscripcionCurso, Procedimiento, TematicaVideo, Proceso
from employees.models import Empleado, Departamento, Tarea
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse
from .forms import CursoForm, DocumentoForm, VideoCursoForm, SlideForm
from django.urls import reverse

@login_required
def ResourcesView(request):
    # --- BLOQUE 1. ACTUALIZACIÓN AUTOMÁTICA Y CIERRE DE CURSOS ---
    hoy = timezone.now().date()
    
    # Identificamos los cursos que vencieron
    cursos_vencidos_qs = Curso.objects.filter(
        estado=Curso.Estado.ACTIVO,
        fecha__lt=hoy
    )
    
    # Actualizamos las inscripciones a 'COMPLETADO' para esos cursos
    InscripcionCurso.objects.filter(
        curso__in=cursos_vencidos_qs,
        estado=InscripcionCurso.EstadoInscripcion.INSCRITO
    ).update(
        estado=InscripcionCurso.EstadoInscripcion.COMPLETADO,
        fecha_finalizacion=hoy
    )
    
    # Cerramos los cursos físicamente
    cursos_vencidos_qs.update(estado=Curso.Estado.FINALIZADO)

    # --- BLOQUE 2. PERMISOS Y VARIABLES DE USUARIO ---
    is_admin = request.user.groups.filter(name='Administrador').exists()
    is_rh = request.user.groups.filter(name="Recursos Humanos").exists()
    
    try:
        empleado = request.user.empleado 
    except (Empleado.DoesNotExist, AttributeError):
        empleado = None

    # --- BLOQUE 3. PROCESAMIENTO DE FORMULARIOS (POST) ---
    form_with_errors = None

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # 3.1 Guardar Curso
        if form_type == 'curso':
            form_curso = CursoForm(request.POST, request.FILES, prefix='create_curso')
            if form_curso.is_valid():
                form_curso.save()
                messages.success(request, '¡Nuevo curso guardado exitosamente! 👍')
                return redirect(reverse('resources:resources') + '#MisCursos')
            form_with_errors = 'curso'

        # 3.2 Guardar Documento (Corregido para evitar doble guardado)
        elif form_type == 'documento':
            form_documento = DocumentoForm(request.POST, request.FILES, prefix='create_doc')
            if form_documento.is_valid():
                doc = form_documento.save()
                messages.success(request, f'¡Documento "{doc.nombre}" guardado exitosamente! 📄')
                # REDIRECT es vital para limpiar el POST y evitar duplicados
                return redirect(reverse('resources:resources') + '#Formatos')
            form_with_errors = 'documento'

        # 3.3 Guardar Contenido (Video)
        elif form_type == 'video':
            form_video = VideoCursoForm(request.POST, prefix='create_video')
            if form_video.is_valid():
                form_video.save()
                messages.success(request, '¡Nuevo contenido guardado exitosamente! 📹')
                return redirect(reverse('resources:resources') + '#Contenido')
            form_with_errors = 'video'

        # 3.4 Guardar Lote de Slides
        elif form_type == 'slide':
            imagenes_lote = request.FILES.getlist('imagenes_lote')
            mes = request.POST.get('mes')
            anio = request.POST.get('anio')
            activar_ahora = request.POST.get('activar_ahora') == 'on'

            if imagenes_lote:
                # --- PASO NUEVO: DESACTIVACIÓN AUTOMÁTICA ---
                # Si el usuario marcó "Activar ahora", primero ponemos en False 
                # todos los slides que existan para ese mes y año.
                if activar_ahora:
                    Slide.objects.filter(mes=mes, anio=anio).update(is_active=False)

                import os
                for f in imagenes_lote:
                    try:
                        nombre_sin_ext = os.path.splitext(f.name)[0]
                        # Extraer solo números del nombre (ej: "1.jpg" -> 1)
                        orden_detectado = int(''.join(filter(str.isdigit, nombre_sin_ext)))
                        
                        # Ahora actualizamos el existente o creamos uno nuevo
                        # Como ya desactivamos los anteriores arriba, estos entrarán como True
                        Slide.objects.update_or_create(
                            mes=mes, anio=anio, order=orden_detectado,
                            defaults={
                                'image': f,
                                'title': f"Slide {orden_detectado} - {mes}/{anio}",
                                'is_active': activar_ahora  # Se guardan como True
                            }
                        )
                    except ValueError: 
                        continue # Si el archivo no tiene número, lo ignora
                
                messages.success(request, f"Slides de {mes}/{anio} actualizados. Los anteriores han sido archivados (desactivados).")
                return redirect('resources:resources')
            
            form_with_errors = 'slide'

    # --- BLOQUE 4. CARGA DE DATOS PARA LA VISTA (GET) ---
    
    # Inicialización de formularios limpios
    form_curso = CursoForm(prefix='create_curso') 
    form_documento = DocumentoForm(prefix='create_doc')
    form_video = VideoCursoForm(prefix='create_video')
    form_slide = SlideForm(prefix='create_slide')

    # SLIDES ACTIVOS
    slides_activos = Slide.objects.filter(is_active=True)

    # CURSOS (Lógica de Chunks)
    mis_cursos = empleado.cursos_inscritos.filter(estado=Curso.Estado.ACTIVO).order_by('fecha') if empleado else Curso.objects.none()
    
    if empleado and empleado.departamento:
        q_disp = Q(es_general=True) | Q(departamentos_destinados=empleado.departamento)
        cursos_disponibles = Curso.objects.filter(q_disp, estado=Curso.Estado.ACTIVO).exclude(inscritos=empleado).distinct().order_by('fecha')
    else:
        cursos_disponibles = Curso.objects.filter(es_general=True, estado=Curso.Estado.ACTIVO).distinct().order_by('fecha')

    chunk_size = 3
    mis_chunks = [mis_cursos[i:i + chunk_size] for i in range(0, len(mis_cursos), chunk_size)]
    disp_chunks = [cursos_disponibles[i:i + chunk_size] for i in range(0, len(cursos_disponibles), chunk_size)]

    # DOCUMENTACIÓN SECCIÓN EXTERNA (APOYO) - Conserva lógica original
    doc_permission_query = Q() if is_admin else Q(es_general=True)
    if not is_admin and empleado and empleado.departamento:
        doc_permission_query.add(Q(departamentos_destinados=empleado.departamento), Q.OR)

    tipos_externos_ids = TipoDocumento.objects.filter(categoria='externo').values_list('id', flat=True)
    documentos_externos_list = Documento.objects.filter(
        doc_permission_query, estado='activo', tipo_documento_id__in=tipos_externos_ids
    ).distinct().order_by('nombre')

    # DOCUMENTACIÓN SECCIÓN INTERNA (FORMATOS) - Jerarquía Nueva
    # Solo necesitamos los PROCESOS, el resto se carga por AJAX
    all_procesos = Proceso.objects.all().order_by('nombre')
    formatos_internos_list = Documento.objects.filter(
        estado='activo', tipo_documento__categoria='interno'
    ).distinct().order_by('nombre')

    # VIDEOTECA
    video_perm_query = Q() if is_admin else (Q(curso=None) | Q(curso__es_general=True))
    if not is_admin and empleado and empleado.departamento:
        video_perm_query.add(Q(curso__departamentos_destinados=empleado.departamento), Q.OR)
    
    videos_list = VideoCurso.objects.filter(video_perm_query, estado='activo').distinct().order_by('-fecha_registro')

    # CERTIFICADOS E HISTORIAL
    certificados_qs = InscripcionCurso.objects.filter(
        empleado=empleado, certificado__isnull=False, estado__in=['COMPLETADO', 'APROBADO']
    ).select_related('curso').order_by('-fecha_finalizacion')

    # --- BLOQUE 5. CONTEXTO FINAL ---
    context = {
        'empleado': empleado,
        'is_admin': is_admin,
        'is_rh': is_rh,
        'form_curso': form_curso,
        'form_documento': form_documento,
        'form_video': form_video,
        'form_slide': form_slide,
        'form_with_errors': form_with_errors,
        'slides': slides_activos,
        
        'mis_cursos_chunks': mis_chunks,
        'cursos_disponibles_chunks': disp_chunks,
        'todos_los_cursos': Curso.objects.all().order_by('titulo'),
        
        # Formatos (Internos - Nueva Jerarquía)
        'all_procesos': all_procesos, 
        'formatos': Paginator(formatos_internos_list, 4).get_page(1),
        
        # Documentos (Externos - Lógica Original)
        'documentos_generales': Paginator(documentos_externos_list, 4).get_page(1),
        'tipos_para_documentos': TipoDocumento.objects.filter(categoria='externo').order_by('nombre'),
        'all_departamentos': Departamento.objects.all().order_by('nombre'),
        
        'videos_videoteca': Paginator(videos_list, 6).get_page(1),
        'tematicas_video': TematicaVideo.objects.all().order_by('nombre'),
        
        'historial_inicial': Paginator(certificados_qs, 5).get_page(1),
        'certificados_iniciales': Paginator(certificados_qs, 4).get_page(1),
        'all_empleados': Empleado.objects.all().order_by('nombre'),
        
        # Datos para editar modales
        'todos_los_documentos': Documento.objects.all().order_by('nombre'),
        'todos_los_videos': VideoCurso.objects.all().order_by('titulo'),
    }
    
    return render(request, 'resources.html', context)

@login_required 
def BuscarDocumentosView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '')

    depto_id = request.GET.get('departamento', '')
    tipo_id = request.GET.get('tipo', '')
    proc_id = request.GET.get('procedimiento', '')

    is_admin = request.user.groups.filter(name='Administrador').exists()
    is_rh = request.user.groups.filter(name="Recursos Humanos").exists()

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
        filter_query = Q()
    
    documentos_list = Documento.objects.filter(
        permission_query,
        filter_query,
        lookup, 
        tipo_documento__categoria='externo',
        estado='activo'
    )

    if tipo_id:
        documentos_list = documentos_list.filter(tipo_documento__id=tipo_id)

    if proc_id:
        documentos_list = documentos_list.filter(procedimiento_id=proc_id)

    documentos_list = documentos_list.distinct().order_by('nombre')

    paginator = Paginator(documentos_list, 4)
    page_obj = paginator.get_page(page_number)

    html = render_to_string(
        template_name='_documentos_partial.html',
        context={
            'documentos': page_obj,
            'is_admin': is_admin,
            'is_rh': is_rh
        }    
    )

    return JsonResponse({
        'html': html,
        'has_next': page_obj.has_next()
    })

@login_required
def BuscarFormatosView(request):
    # 1. Captura de parámetros
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '')
    proceso_id = request.GET.get('proceso', '')
    proc_id = request.GET.get('procedimiento', '')
    sub_categoria = request.GET.get('sub_categoria', '')

    is_admin = request.user.groups.filter(name='Administrador').exists()

    # 2. QuerySet Base (Solo Internos y Activos)
    documentos_qs = Documento.objects.filter(
        tipo_documento__categoria='interno',
        estado='activo'
    )

    # 3. Aplicación de Filtros Jerárquicos
    if proceso_id:
        documentos_qs = documentos_qs.filter(procedimiento__proceso_id=proceso_id)

    if proc_id:
        documentos_qs = documentos_qs.filter(procedimiento_id=proc_id)
        # Solo filtramos por Manual/Formato si ya hay un procedimiento o búsqueda específica
        if sub_categoria:
            documentos_qs = documentos_qs.filter(tipo_documento__sub_categoria=sub_categoria)

    # 4. Búsqueda por texto
    if query:
        lookup = (
            Q(nombre__icontains=query) |
            Q(codigo_documento__icontains=query) |
            Q(palabras_clave__icontains=query)
        )
        documentos_qs = documentos_qs.filter(lookup)

    # 5. ELIMINACIÓN DEFINITIVA DE DUPLICADOS
    # Extraemos IDs únicos y re-filtramos. Esto es lo más robusto para paginación AJAX.
    ids_unicos = documentos_qs.values_list('id', flat=True).distinct()
    # Ordenamos por nombre e ID para que la "página 2" nunca repita elementos de la "página 1"
    documentos_list = Documento.objects.filter(id__in=ids_unicos).order_by('nombre', 'id')

    # 6. Paginación
    paginator = Paginator(documentos_list, 4)
    page_obj = paginator.get_page(page_number)

    html = render_to_string(
        template_name='_documentos_partial.html',
        context={
            'documentos': page_obj,
            'is_admin': is_admin
        },
        request=request
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
    
    if curso.modalidad == Curso.Modalidad.AUTOINSCRIPCION: 
        
        inscripcion, creado = InscripcionCurso.objects.get_or_create(
            curso=curso,
            empleado=empleado,
            defaults={
                'fecha_finalizacion': curso.fecha,
                'estado': InscripcionCurso.EstadoInscripcion.INSCRITO 
            }
        )
        
        if creado:
            curso.inscritos.add(empleado)

            url_curso = request.build_absolute_uri(
                reverse('resources:resources')
            )

            Tarea.objects.create(
                empleado=empleado,
                titulo=f"Completar curso: {curso.titulo}",
                descripcion=(
                    f"Te has inscrito voluntariamente al curso '{curso.titulo}'. "
                    f"Recuerda que la fecha límite es el {curso.fecha}."
                ),
                fecha_vencimiento=curso.fecha,
                prioridad=Tarea.Prioridad.ALTA, 
                estado=Tarea.EstadoTarea.PENDIENTE,
                enlace=curso.link or '',
            )
            
            messages.success(request, f"¡Inscripción exitosa! Se ha añadido '{curso.titulo}' a tus tareas pendientes. 🎉")
        else:
            messages.info(request, f"Ya estás inscrito en '{curso.titulo}'. Revisa tus tareas pendientes.")
                
    elif curso.modalidad != Curso.Modalidad.AUTOINSCRIPCION:
        messages.error(request, "Este curso requiere solicitud de inscripción manual.")

    return redirect('resources:resources')

@login_required
def BuscarVideosView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '')
    depto_id = request.GET.get('departamento', '')
    tematica_id = request.GET.get('tematica', '')

    is_admin = request.user.groups.filter(name='Administrador').exists()

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

    videos_list = VideoCurso.objects.filter(permission_query, estado='activo')

    if query:
        lookup = (
            Q(titulo__icontains=query) |
            Q(ponente__icontains=query) |
            Q(curso__titulo__icontains=query)
        )
        videos_list = videos_list.filter(lookup)

    if depto_id:
        videos_list = videos_list.filter(departamentos_destinados__id=depto_id)

    if tematica_id:
        videos_list = videos_list.filter(tematica_id=tematica_id)

    videos_list = videos_list.distinct().order_by('-fecha_registro')

    paginator = Paginator(videos_list, 6)
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

def is_admin_or_rh_check(user):
    # Permite si es Admin O Recursos Humanos
    return user.is_authenticated and (
        user.groups.filter(name='Administrador').exists() or 
        user.groups.filter(name='Recursos Humanos').exists()
    )

@user_passes_test(is_admin_or_rh_check)
def CursoEditView(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    if request.method == 'POST':
        form = CursoForm(request.POST, request.FILES, instance=curso, prefix='edit')
        
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Curso "{curso.titulo}" actualizado exitosamente!')
            return redirect(reverse('resources:resources') + '#MisCursos')
        else:
            messages.warning(request, 'Hubo un error al actualizar. Revisa los campos.')
            pass 
            
    else:
        form = CursoForm(instance=curso, prefix='edit')

    return render(request, '_curso_edit_form.html', {
        'form': form
    })

@user_passes_test(is_admin_or_rh_check)
def edit_documento(request, documento_id):

    documento = get_object_or_404(Documento, id=documento_id)
    
    if request.method == 'POST':
        # El usuario está enviando el formulario actualizado
        form = DocumentoForm(request.POST, request.FILES, instance=documento, prefix="edit-doc")
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Documento "{documento.nombre}" actualizado con éxito.')
            return redirect(reverse('resources:resources') + '#Documentos')
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

@user_passes_test(is_admin_or_rh_check)
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
            return redirect(reverse('resources:resources') + '#Contenido')
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

@user_passes_test(is_admin_or_rh_check)
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

def BuscarCertificadosView(request):
    # Parámetros de la solicitud AJAX
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '')
    
    # Manejar caso de empleado no encontrado si fuera necesario, aunque login_required ayuda
    empleado = None
    try:
        empleado = request.user.empleado
    except (Empleado.DoesNotExist, AttributeError):
        # Si no hay empleado, la QS estará vacía, lo cual es correcto.
        pass

    certificados_qs = InscripcionCurso.objects.filter(
        empleado=empleado, 
        certificado__isnull=False, 
        estado__in=['COMPLETADO', 'APROBADO']
    ).select_related('curso').order_by('-fecha_finalizacion') 

    # Aplicar filtro de búsqueda
    if query:
        certificados_qs = certificados_qs.filter(
            Q(curso__titulo__icontains=query) | 
            Q(curso__descripcion__icontains=query)
        )
    
    # Paginación
    paginator = Paginator(certificados_qs, 4)
    page_obj = paginator.get_page(page_number)

    # 1. Usar render_to_string para generar el HTML del partial
    html_content = render_to_string(
        template_name='_certificados_partial.html',
        context={'certificados': page_obj} 
    )

    return JsonResponse({
        'html': html_content,
        'has_next': page_obj.has_next(), 
    })

@login_required
def GetHistorialEmpleadoView(request):
    """
    Obtiene el historial de cursos de un empleado específico y devuelve
    la tabla HTML parcial para el modal de edición.
    """
    empleado_id = request.GET.get('empleado_id')
    
    if not empleado_id:
        return JsonResponse({'error': 'No ID provided'}, status=400)
    
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    # Obtenemos todas las inscripciones del empleado ordenadas
    inscripciones = InscripcionCurso.objects.filter(empleado=empleado).order_by('-fecha_inscripcion')
    
    html = render_to_string('_historial_empleado_table.html', {
        'inscripciones': inscripciones,
        'empleado': empleado
    }, request=request)
    
    return JsonResponse({'html': html})

@login_required
def UpdateCertificacionView(request, inscripcion_id):
    """
    Actualiza una sola fila (inscripción) desde el modal: Estado, Calificación o Archivo.
    """
    if request.method == 'POST':
        inscripcion = get_object_or_404(InscripcionCurso, id=inscripcion_id)
        
        # Datos del formulario AJAX
        nuevo_estado = request.POST.get('estado')
        nueva_calif = request.POST.get('calificacion')
        nuevo_certificado = request.FILES.get('certificado') # Archivo
        
        try:
            # 1. Actualizar Estado
            if nuevo_estado:
                inscripcion.estado = nuevo_estado
            
            # 2. Actualizar Calificación
            if nueva_calif:
                inscripcion.calificacion = float(nueva_calif)
            elif nueva_calif == '':
                # Si viene vacío, lo ponemos nulo
                inscripcion.calificacion = None
                
            # 3. Actualizar Certificado
            if nuevo_certificado:
                inscripcion.certificado = nuevo_certificado
                # Si subimos certificado y no hay fecha de fin, ponemos hoy
                if not inscripcion.fecha_finalizacion:
                     inscripcion.fecha_finalizacion = timezone.now().date()

            inscripcion.save()
            return JsonResponse({'status': 'success', 'message': 'Actualizado correctamente'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)

@login_required
def BuscarHistorialView(request):
    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    
    is_admin = request.user.groups.filter(name='Administrador').exists()
    is_rh = request.user.groups.filter(name="Recursos Humanos").exists()

    if not hasattr(request.user, 'empleado'):
        return JsonResponse({'html': '', 'has_next': False})

    estados_finalizados = [
        InscripcionCurso.EstadoInscripcion.COMPLETADO,
        InscripcionCurso.EstadoInscripcion.APROBADO,
        InscripcionCurso.EstadoInscripcion.RECHAZADO,
        InscripcionCurso.EstadoInscripcion.DADO_DE_BAJA,
    ]

    historial = InscripcionCurso.objects.filter(
        empleado=request.user.empleado,
        estado__in=estados_finalizados
    ).select_related('curso', 'empleado')

    if query:
        historial = historial.filter(
            Q(curso__titulo__icontains=query) | 
            Q(fecha_finalizacion__icontains=query)
        )
    
    historial = historial.order_by('-fecha_finalizacion', '-fecha_inscripcion')

    # Paginación
    paginator = Paginator(historial, 5) # Muestra 5 cursos por carga
    page_obj = paginator.get_page(page_number)

    # Renderizado del parcial
    # Nota: Pasamos 'historial' como contexto.
    html = render_to_string('_historial_partial.html', {
        'historial': page_obj,
        'is_admin': is_admin,
        'is_rh': is_rh,
        'user': request.user
    }, request=request)

    return JsonResponse({
        'html': html,
        'has_next': page_obj.has_next()
    })

@login_required
def GetProcesosView(request):
    procesos = Proceso.objects.all().values('id', 'nombre').order_by('nombre')
    return JsonResponse(list(procesos), safe=False)

@login_required
def GetProcedimientosView(request):
    proceso_id = request.GET.get('proceso_id')
    if not proceso_id:
        return JsonResponse([], safe=False)
    
    # Obtenemos los procedimientos que pertenecen a ese proceso
    # Opcional: Solo traer los que tienen documentos internos asociados
    procedimientos = Procedimiento.objects.filter(proceso_id=proceso_id).values('id', 'nombre').order_by('nombre')
    return JsonResponse(list(procedimientos), safe=False)