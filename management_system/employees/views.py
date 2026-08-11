from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from .models import Empleado, Departamento, Expediente, Vacacion, Tarea, Incapacidad, ConfiguracionRH
from equipment.models import Equipo, AsignacionEquipo
from django.http import JsonResponse
import json
import os
import unicodedata
from django.db import transaction
from service_stations.models import ServiceStation
from django.contrib import messages
from .forms import EmpleadoForm, VacacionForm
from django.db.models import Q, Max, Prefetch
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
import base64
from django.core.files.storage import default_storage
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils import timezone
from django.urls import reverse
from .signals import crear_documentos_base
from .utils import crear_tarea

def is_admin_check(user):
    return user.is_authenticated and user.groups.filter(name='Administrador').exists()

@login_required
def get_jefes_departamento(request):
    try:
        # 1. Tomamos el empleado del usuario logueado
        empleado = request.user.empleado  # OneToOneField desde Empleado → User
        
        if not empleado.departamento:
            return JsonResponse({
                'success': False,
                'mensaje': 'El empleado no tiene departamento asignado.'
            })

        departamento = empleado.departamento

        # 2. Buscamos todos los jefes de ese departamento

        jefes = [{'id': j.id, 'nombre': j.nombre} for j in departamento.jefe.all()]

        if not jefes:
            return JsonResponse({
                'success': False,
                'mensaje': f'El departamento "{departamento.nombre}" no tiene jefe asignado.'
            })

        return JsonResponse({
            'success': True,
            'departamento': departamento.nombre,
            'jefes': jefes
        })

    except Empleado.DoesNotExist:
        return JsonResponse({
            'success': False,
            'mensaje': 'Tu usuario no tiene un empleado asociado.'
        }, status=404)
    except AttributeError:
        return JsonResponse({
            'success': False,
            'mensaje': 'No se pudo obtener el perfil del empleado.'
        }, status=400)

@login_required
def EmployeesView(request):
    try:
        empleado_logueado = request.user.empleado 
    except:
        empleado_logueado = None
    
    # --- 1. FORMULARIOS INICIALES ---
    form_empleado = EmpleadoForm(prefix='create_empleado')
    form_empleado_edit = EmpleadoForm(prefix='edit_empleado')
    form_vacaciones = VacacionForm(prefix='create_vacaciones')
    form_with_errors = None

    # --- 2. PROCESAMIENTO DE CREACIÓN (POST) ---
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'empleado':
            form_empleado = EmpleadoForm(request.POST, request.FILES, prefix='create_empleado')             
            if form_empleado.is_valid():
                empleado_nuevo = form_empleado.save()
                firma_b64 = request.POST.get('firma_b64')

                if firma_b64:
                    try:
                        format, imgstr = firma_b64.split(';base64,') 
                        ext = format.split('/')[-1]
                        file_data = ContentFile(base64.b64decode(imgstr))
                        file_name = f"firma_{empleado_nuevo.nombre.replace(' ', '_')}.{ext}"
                        empleado_nuevo.firma_digital.save(file_name, file_data, save=False)
                    except Exception as e:
                        print(f"Error guardando firma: {e}")    
                
                empleado_nuevo.save()
                form_empleado.save_m2m()

                # Si se hizo la petición desde AJAX, respondemos con JSON para actualizar solo el formulario sin recargar toda la página
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'message': f'Empleado "{empleado_nuevo.nombre}" guardado exitosamente!'
                    })

                messages.success(request, f'¡Empleado "{empleado_nuevo.nombre}" guardado exitosamente!')                
                return redirect('employees:employees')
            else:

                # Si la validación falla y es una petición AJAX, respondemos con los errores para mostrarlos en el formulario sin recargar toda la página
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': form_empleado.errors})
                
                messages.error(request, 'Error al guardar el empleado. Revisa los campos.')
                form_with_errors = 'empleado'

    # --- 3. CAPTURA DE FILTROS (COMPARTIDOS Y ESPECÍFICOS) ---
    query = request.GET.get('q', '')
    depto_id = request.GET.get('depto_id', '')
    estacion_id = request.GET.get('estacion_id', '')
    
    # Filtros por pestaña
    estado_vac_filtro = request.GET.get('estado', '') # Vacaciones
    # --- BLOQUE A: LÓGICA DE EMPLEADOS ---
    lookup_emp = Q()
    if query:
        lookup_emp = (
            Q(nombre__icontains=query) |
            Q(email__icontains=query) |
            Q(posicion__icontains=query) |
            Q(user__username__icontains=query, user__isnull=False) 
        )

    empleados_qs = Empleado.objects.filter(
        lookup_emp,
        estado=Empleado.EstadoEmpleado.ACTIVO
    )

    equipos_activos_prefetch = Prefetch(
        'equipos_asignados',
        queryset=AsignacionEquipo.objects.filter(
            fecha_devolucion__isnull=True
        ).select_related('equipo__tipo_equipo', 'equipo__estado_fisico')
    )

    # Agregamos el prefetch de equipos a la consulta principal
    empleados_activos = empleados_qs.prefetch_related(
        'expedientes', 
        'incapacidades',
        equipos_activos_prefetch
    ).order_by('nombre').distinct()

    if depto_id:
        empleados_qs = empleados_qs.filter(departamento__id=depto_id)
    if estacion_id:
        empleados_qs = empleados_qs.filter(estacion_servicio__id=estacion_id)

    # Prefetch para optimizar los contadores en las tarjetas
    empleados_activos = empleados_qs.prefetch_related('expedientes', 'incapacidades').order_by('nombre').distinct()

    paginator_emp = Paginator(empleados_activos, 6)
    empleados_page = paginator_emp.get_page(request.GET.get('page', 1))

    # --- BLOQUE B: LÓGICA DE VACACIONES ---
    vacaciones_qs = Vacacion.objects.select_related('empleado', 'autorizador')

    # 1. Definir roles
    is_admin = request.user.groups.filter(name='Administrador').exists()
    is_rh = request.user.groups.filter(name='Recursos Humanos').exists()
    es_jefe = Departamento.objects.filter(jefe=empleado_logueado).exists()

    # 2. Aplicar jerarquía
    if is_admin or is_rh:
        # Ver todo
        vacaciones_qs = vacaciones_qs.all()

    elif es_jefe:
        # Obtener los departamentos donde este empleado es jefe
        deptos_del_jefe = Departamento.objects.filter(jefe=empleado_logueado)
        # Filtrar vacaciones de empleados que pertenezcan a esos departamentos
        vacaciones_qs = vacaciones_qs.filter(empleado__departamento__in=deptos_del_jefe)

    elif empleado_logueado:
        # Empleado normal: solo las suyas
        vacaciones_qs = vacaciones_qs.filter(empleado=empleado_logueado)

    else:
        vacaciones_qs = vacaciones_qs.none()

    if query:
        vacaciones_qs = vacaciones_qs.filter(empleado__nombre__icontains=query)
    if depto_id:
        vacaciones_qs = vacaciones_qs.filter(empleado__departamento__id=depto_id)
    if estacion_id:
        vacaciones_qs = vacaciones_qs.filter(empleado__estacion_servicio__id=estacion_id)
    if estado_vac_filtro:
        vacaciones_qs = vacaciones_qs.filter(estado=estado_vac_filtro)
    
    vac_paginator = Paginator(vacaciones_qs.order_by('-fecha_solicitud'), 6)
    vacaciones_page = vac_paginator.get_page(request.GET.get('vac_page', 1))


    # --- BLOQUE C: LÓGICA DE INCAPACIDADES ---
    incapacidades_qs = Incapacidad.objects.select_related('empleado', 'empleado__departamento')

    if is_admin or is_rh:
        pass
    elif es_jefe:
        deptos_del_jefe = Departamento.objects.filter(jefe=empleado_logueado)
        incapacidades_qs = incapacidades_qs.filter(empleado__departamento__in=deptos_del_jefe)
    elif empleado_logueado:
        incapacidades_qs = incapacidades_qs.filter(empleado=empleado_logueado)
    else:
        incapacidades_qs = incapacidades_qs.none()

    if query:
        incapacidades_qs = incapacidades_qs.filter(empleado__nombre__icontains=query)
    if depto_id:
        incapacidades_qs = incapacidades_qs.filter(empleado__departamento__id=depto_id)
    if estacion_id:
        incapacidades_qs = incapacidades_qs.filter(empleado__estacion_servicio__id=estacion_id)

    incapacidades_qs = incapacidades_qs.order_by('-fecha_inicio')

    inca_paginator = Paginator(incapacidades_qs, 6)
    incapacidades_page = inca_paginator.get_page(request.GET.get('inca_page', 1))

    # --- 4. DATOS COMPLEMENTARIOS ---
    all_departamentos = Departamento.objects.all().order_by('nombre')
    all_estaciones = ServiceStation.objects.all().order_by('nombre')
    todas_las_vacaciones = vacaciones_qs.order_by('-fecha_solicitud')

    empleados_rh = Empleado.objects.filter(
        departamento__nombre__icontains="RH", 
        estado=Empleado.EstadoEmpleado.ACTIVO
    ).order_by('nombre')
    todos_los_empleados_qs = Empleado.objects.filter(estado=Empleado.EstadoEmpleado.ACTIVO).order_by('nombre')

    empleados_mi_depto = Empleado.objects.none()
    if empleado_logueado and empleado_logueado.departamento:
        empleados_mi_depto = Empleado.objects.filter(
            departamento=empleado_logueado.departamento,
            estado=Empleado.EstadoEmpleado.ACTIVO
        ).order_by('nombre')

    # Intentar obtener el empleado del usuario logueado
    try:
        empleado_logueado = request.user.empleado 
    except Empleado.DoesNotExist:
        empleado_logueado = None

    context = {
        'empleado': empleado_logueado,
        'is_admin': is_admin,
        'is_rh': is_rh,
        'form_with_errors': form_with_errors,
        'form_empleado': form_empleado,
        'form_empleado_edit': form_empleado_edit,
        'form_vacaciones': form_vacaciones,
        'todas_las_vacaciones': todas_las_vacaciones,

        'todos_los_empleados': todos_los_empleados_qs,
        'empleados_mi_depto': empleados_mi_depto,

        'vista_agrupada': is_admin or is_rh or es_jefe,

        # Paginaciones
        'empleados_page': empleados_page,
        'vacaciones_page': vacaciones_page,
        'incapacidades_page': incapacidades_page,
        
        # Selects y Filtros
        'all_departamentos': all_departamentos,
        'all_estaciones': all_estaciones,
        'responsables_rh': empleados_rh,
        'current_q': query,
        'current_depto_id': depto_id,
        'current_estacion_id': estacion_id,
        'estados_vacacion': Vacacion.EstadoVacacion.choices,
    }
    return render(request, 'employees.html', context)

@login_required
def SearchEmployeesView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '')
    depto_id = request.GET.get('depto_id', '')
    estacion_id = request.GET.get('estacion_id', '')

    lookup = Q()
    if query:
        lookup = (
            Q(nombre__icontains=query) |
            Q(email__icontains=query) |
            Q(posicion__icontains=query) |
            Q(user__username__icontains=query, user__isnull=False)
        )

    depto_query = Q()
    if depto_id:
        depto_query = Q(departamento__id=depto_id)

    estacion_query = Q()
    if estacion_id:
        estacion_query = Q(estacion_servicio__id=estacion_id)

    equipos_activos_prefetch = Prefetch(
        'equipos_asignados',
        queryset=AsignacionEquipo.objects.filter(
            fecha_devolucion__isnull=True
        ).select_related('equipo__tipo_equipo', 'equipo__estado_fisico')
    )

    empleados_activos = Empleado.objects.filter(
        lookup,
        depto_query,
        estacion_query,
        estado=Empleado.EstadoEmpleado.ACTIVO,
    ).prefetch_related(
        'expedientes', 
        equipos_activos_prefetch
    ).distinct().order_by('nombre')

    paginator = Paginator(empleados_activos, 6)
    empleados_page = paginator.get_page(page_number)

    html = render_to_string(
         '_employee_cards.html',
        {
            'empleados_page': empleados_page, 
            'is_admin': request.user.groups.filter(name='Administrador').exists(),
            'is_rh': request.user.groups.filter(name='Recursos Humanos').exists()

        },
        request=request
    ) 

    return JsonResponse({
        'html': html,
        'has_next': empleados_page.has_next()
    })

@login_required
def AddVacacionSolicitudView(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        form = VacacionForm(request.POST, request.FILES, prefix='create_vacaciones')
        
        if form_type == 'solicitar_vacaciones':
            autorizador_id = request.POST.get('autorizador')
            gerente = ConfiguracionRH.get_gerente()
            
            # Los checkboxes solo envían valor si están marcados ('on')
            requiere_respuesta = request.POST.get('requiere_respuesta_automatica') == 'on'
            requiere_redireccion = request.POST.get('requiere_redireccion') == 'on'
            # getlist es necesario para capturar múltiples opciones de un <select multiple>
            empleados_redireccion_ids = request.POST.getlist('empleados_redireccion')
            
            fechas_raw = request.POST.get('create_vacaciones-dias_seleccionados')
            
            try:
                # Convertimos el string JSON a una lista de Python
                lista_fechas = json.loads(fechas_raw) if fechas_raw else []
            except json.JSONDecodeError:
                # Si falla el JSON, intentamos split por coma por si acaso
                lista_fechas = [d.strip() for d in fechas_raw.split(',')] if fechas_raw else []

            # 2. Validación: Al menos un día seleccionado
            if not lista_fechas:
                messages.error(request, "Debes seleccionar al menos un día en el calendario.")
                return redirect(reverse('employees:employees') + '#vacaciones-content')
            
            lista_fechas.sort()

            # --- NUEVA LÓGICA PARA DÍAS SEPARADOS ---
            if len(lista_fechas) == 1:
                rango_dias = f"el día {lista_fechas[0]}"
            elif len(lista_fechas) == 2:
                rango_dias = f"los días {lista_fechas[0]} y {lista_fechas[1]}"
            else:
                # Une todos con coma excepto el último, que se une con "y"
                dias_str = ", ".join(lista_fechas[:-1]) + f" y {lista_fechas[-1]}"
                rango_dias = f"los días {dias_str}"
            # ----------------------------------------

            try:
                with transaction.atomic():
                    autorizador = None
                    if autorizador_id:
                        autorizador = get_object_or_404(Empleado, id=autorizador_id)
                    
                    vacacion = Vacacion(
                        empleado=request.user.empleado,
                        dias_seleccionados=lista_fechas,
                        estado='PENDIENTE',
                        autorizador=autorizador,
                        gerente_autorizador=gerente,
                        observaciones=request.POST.get('create_vacaciones-observaciones', ''),
                        requiere_respuesta_automatica=requiere_respuesta,
                        requiere_redireccion=requiere_redireccion,
                    )
                    
                    # Archivos opcionales
                    if request.FILES.get('create_vacaciones-archivo_vacaciones'):
                        vacacion.archivo_vacaciones = request.FILES['create_vacaciones-archivo_vacaciones']
                    if request.FILES.get('create_vacaciones-archivo_roles'):
                        vacacion.archivo_roles = request.FILES['create_vacaciones-archivo_roles']
                    
                    vacacion.save()

                    # --- Asignación de empleados de redirección (ManyToMany) ---
                    if requiere_redireccion and empleados_redireccion_ids:
                        vacacion.empleados_redireccion.set(empleados_redireccion_ids)

                    empleado_solicitante = vacacion.empleado
                    jefe_asignado = vacacion.autorizador
                    url_vacaciones = request.build_absolute_uri(
                        reverse('employees:employees') + '#vacaciones-content'
                    )

                    # Texto descriptivo para las tareas
                    total = f"({len(lista_fechas)} días en total)"

                    # 1. Tarea para el Jefe Asignado
                    if jefe_asignado:
                        crear_tarea(
                            empleado=jefe_asignado,
                            titulo=f"Autorizar Vacaciones #{vacacion.id}: {empleado_solicitante.nombre}",
                            descripcion=f"El empleado solicita vacaciones {rango_dias} {total}. Requiere autorización.",
                            prioridad=Tarea.Prioridad.ALTA,
                            fecha_vencimiento=lista_fechas[0],
                            enlace=url_vacaciones,
                            objeto_id=vacacion.id,
                            tipo_objeto="vacacion"
                        )

                    # 2. Tarea para el Gerente (si existe y es distinto al jefe)
                    if gerente and gerente != jefe_asignado:
                        crear_tarea(
                            empleado=gerente,
                            titulo=f"Autorizar Vacaciones #{vacacion.id}: {empleado_solicitante.nombre}",
                            descripcion=f"Solicitud {rango_dias} {total}. Requiere autorización de Gerencia.",
                            prioridad=Tarea.Prioridad.ALTA,
                            fecha_vencimiento=lista_fechas[0],
                            enlace=url_vacaciones,
                            objeto_id=vacacion.id,
                            tipo_objeto="vacacion"
                        )

                    personal_rh = Empleado.objects.filter(
                        departamento__nombre__icontains="Recursos Humanos",
                        estado='ACTIVO'
                    )

                    # 3. Tareas para Recursos Humanos
                    for empleado_rh in personal_rh:
                        crear_tarea(
                            empleado=empleado_rh,
                            titulo=f"Gestionar solicitud de vacaciones #{vacacion.id}: {empleado_solicitante.nombre}",
                            descripcion=f"Nueva solicitud pendiente de aprobación por parte de {jefe_asignado.nombre if jefe_asignado else 'Jefe'}.",
                            prioridad=Tarea.Prioridad.BAJA,
                            fecha_vencimiento=lista_fechas[0],
                            enlace=url_vacaciones,
                            objeto_id=vacacion.id,
                            tipo_objeto="vacacion"
                        )

                    # 4. Tarea para el Empleado Solicitante
                    crear_tarea(
                        empleado=empleado_solicitante,
                        titulo=f"Darle seguimiento a tus vacaciones #{vacacion.id}",
                        descripcion=f"Has enviado tu solicitud {rango_dias} {total}. Mantente al tanto de la resolución de {jefe_asignado.nombre if jefe_asignado else 'tu jefe'}.",
                        prioridad=Tarea.Prioridad.MEDIA,
                        fecha_vencimiento=lista_fechas[0],
                        enlace=url_vacaciones,
                        objeto_id=vacacion.id,
                        tipo_objeto="vacacion"
                    )

                    messages.success(request, "Solicitud enviada. Se han generado tareas de seguimiento. ⏳")

            except Exception as e:
                messages.error(request, f"Error al procesar la solicitud: {e}")

        else:
            # Flujo original para RH/Admin (usa el form completo con prefijo)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        vacacion = form.save(commit=False)
                        vacacion.estado = 'PENDIENTE'
                        vacacion.save()
                        form.save_m2m()
                        messages.success(request, "Vacación registrada correctamente.")
                except Exception as e:
                    messages.error(request, f"Error: {e}")
            else:
                messages.error(request, "Datos inválidos. Revisa el formulario.")

    return redirect(reverse('employees:employees') + '#vacaciones-content')

@login_required
def FirmarVacacionView(request, vacacion_id):
    if request.method == "POST":
        vacacion = get_object_or_404(Vacacion, id=vacacion_id)
        accion = request.POST.get('accion')
        empleado_actual = request.user.empleado
        ahora = timezone.now()

        es_jefe    = vacacion.autorizador == empleado_actual
        es_gerente = vacacion.gerente_autorizador == empleado_actual

        if accion == 'FIRMAR':
            if es_jefe and not vacacion.autorizador_firmado:
                vacacion.autorizador_firmado = True
                vacacion.autorizador_fecha_firma = ahora
                messages.success(request, f"Firmaste como Jefe de Departamento. ✅")
                
                # 1. Completar ÚNICAMENTE la tarea del Jefe que acaba de firmar
                Tarea.objects.filter(
                    empleado=empleado_actual,
                    objeto_id=vacacion.id,
                    tipo_objeto="vacacion",
                    estado=Tarea.EstadoTarea.PENDIENTE
                ).update(
                    estado=Tarea.EstadoTarea.COMPLETADA,
                    fecha_completado=ahora
                )

            elif es_gerente and not vacacion.gerente_firmado:
                vacacion.gerente_firmado = True
                vacacion.gerente_fecha_firma = ahora
                messages.success(request, f"Firmaste como Gerente. ✅")
                
                # 2. Completar ÚNICAMENTE la tarea del Gerente que acaba de firmar
                Tarea.objects.filter(
                    empleado=empleado_actual,
                    objeto_id=vacacion.id,
                    tipo_objeto="vacacion",
                    estado=Tarea.EstadoTarea.PENDIENTE
                ).update(
                    estado=Tarea.EstadoTarea.COMPLETADA,
                    fecha_completado=ahora
                )

            else:
                messages.warning(request, "No tienes permisos para firmar esta solicitud o ya fue firmada.")

            # --- EVALUACIÓN DE APROBACIÓN TOTAL ---
            if vacacion.autorizador_firmado and vacacion.gerente_firmado:
                vacacion.estado = 'APROBADO'
                
                # 3. Completar TODAS las tareas restantes (Recursos Humanos y Empleado Solicitante)
                Tarea.objects.filter(
                    objeto_id=vacacion.id,
                    tipo_objeto="vacacion",
                    estado=Tarea.EstadoTarea.PENDIENTE
                ).update(
                    estado=Tarea.EstadoTarea.COMPLETADA,
                    fecha_completado=ahora
                )
                messages.success(request, f"¡Ambas firmas completas! Vacación de {vacacion.empleado.nombre} APROBADA.")

        elif accion == 'RECHAZAR':
            vacacion.estado = 'RECHAZADO'
            
            # 4. Si se rechaza, pasamos todas las tareas pendientes a FINALIZADA (u otro estado de cierre)
            Tarea.objects.filter(
                objeto_id=vacacion.id,
                tipo_objeto="vacacion",
                estado=Tarea.EstadoTarea.PENDIENTE
            ).update(
                estado=Tarea.EstadoTarea.FINALIZADA,
                fecha_completado=ahora # Opcional guardar cuándo terminó el flujo
            )
            messages.warning(request, "Solicitud rechazada.")

        vacacion.save()

    return redirect(reverse('employees:employees') + '#vacaciones-content')

@login_required
def SearchVacationsView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '')
    depto_id = request.GET.get('depto_id', '')
    estacion_id = request.GET.get('estacion_id', '')
    estado_filtro = request.GET.get('estado', '')
    fecha_desde_vac = request.GET.get('fecha_desde', '')
    fecha_hasta_vac = request.GET.get('fecha_hasta', '')

    try:
        empleado_logueado = request.user.empleado
    except:
        empleado_logueado = None

    is_admin = request.user.groups.filter(name='Administrador').exists()
    is_rh = request.user.groups.filter(name='Recursos Humanos').exists()
    es_jefe = Departamento.objects.filter(jefe=empleado_logueado).exists()

    print(f"Usuario: {request.user.username}")
    print(f"is_admin: {is_admin}")
    print(f"is_rh: {is_rh}")
    print(f"es_jefe: {es_jefe}")
    print(f"empleado_logueado: {empleado_logueado}")
    print(f"Grupos: {list(request.user.groups.values_list('name', flat=True))}")


    # Empezamos con todos los registros
    vacaciones_qs = Vacacion.objects.select_related('empleado', 'autorizador').all()

    if is_admin or is_rh:
        vacaciones_qs = vacaciones_qs.all()
    elif es_jefe:
        deptos_del_jefe = Departamento.objects.filter(jefe=empleado_logueado)
        vacaciones_qs = vacaciones_qs.filter(empleado__departamento__in=deptos_del_jefe)
    elif empleado_logueado:
        vacaciones_qs = vacaciones_qs.filter(empleado=empleado_logueado)
    else:
        vacaciones_qs = vacaciones_qs.none()

    print(f"Total vacaciones encontradas: {vacaciones_qs.count()}")

    # Filtro 1: Búsqueda por texto (Nombre del empleado, email o posición)
    if query:
        vacaciones_qs = vacaciones_qs.filter(
            Q(empleado__nombre__icontains=query) |
            Q(empleado__email__icontains=query)
        )

    # Filtro 2: Por Departamento del empleado
    if depto_id:
        vacaciones_qs = vacaciones_qs.filter(empleado__departamento__id=depto_id)

    # Filtro 3: Por Estación del empleado
    if estacion_id:
        vacaciones_qs = vacaciones_qs.filter(empleado__estacion_servicio__id=estacion_id)

    # Filtro 4: Por Estado de la solicitud de vacaciones
    if estado_filtro:
        vacaciones_qs = vacaciones_qs.filter(estado=estado_filtro)

    # Filtro 5: Por Fecha de Inicio y Fin de las vacaciones
    if fecha_desde_vac:
        vacaciones_qs = vacaciones_qs.filter(fecha_inicio__gte=fecha_desde_vac)
    if fecha_hasta_vac:
        vacaciones_qs = vacaciones_qs.filter(fecha_fin__lte=fecha_hasta_vac)

    # Ordenamiento: Más recientes primero
    vacaciones_qs = vacaciones_qs.order_by('-fecha_solicitud')

    # Paginación (6 por página para mantener consistencia con empleados)
    paginator = Paginator(vacaciones_qs, 6)
    vacaciones_page = paginator.get_page(page_number)

    # Renderizamos solo el fragmento de las tarjetas
    html = render_to_string(
        '_vacation_cards.html',
        {
            'vacaciones_page': vacaciones_page,
            'is_admin': request.user.groups.filter(name='Administrador').exists(),
            'is_rh': request.user.groups.filter(name='Recursos Humanos').exists(),
            'empleado': empleado_logueado,
        },
        request=request
    )

    return JsonResponse({
        'html': html,
        'has_next': vacaciones_page.has_next()
    })

@login_required
def EditVacacionView(request, vacacion_id):
    vacacion = get_object_or_404(Vacacion, id=vacacion_id)
    
    if request.method == 'POST':
        # 1. Procesar Días Seleccionados (JSON)
        dias_json = request.POST.get('dias_seleccionados')
        if dias_json:
            try:
                nuevos_dias = json.loads(dias_json)
                # Solo actualiza si realmente hay días seleccionados
                if nuevos_dias:
                    vacacion.dias_seleccionados = nuevos_dias
                    sorted_dias = sorted(nuevos_dias)
                    vacacion.fecha_inicio = sorted_dias[0]
                    vacacion.fecha_fin = sorted_dias[-1]
            except ValueError:
                pass

        # 2. Datos Básicos y Autorización

        nuevo_estado = request.POST.get('estado')
        se_resetearon_firmas = False  # <--- Bandera para saber si disparamos tareas
        
        # --- LÓGICA  PARA RESETEAR FIRMAS ---
        # Si la vacación en la Base de Datos ya estaba firmada/aprobada/rechazado y  el frontend nos envía que el nuevo estado es PENDIENTE
        # limpiamos todas las firmas obligatoriamente.
        if request.POST.get('reset_firmas') == 'true' or (vacacion.estado in ['APROBADO', 'RECHAZADO'] and nuevo_estado == 'PENDIENTE'):
            vacacion.autorizador_firmado = False
            vacacion.autorizador_fecha_firma = None
            vacacion.gerente_firmado = False
            vacacion.gerente_fecha_firma = None
            vacacion.estado = 'PENDIENTE'
            se_resetearon_firmas = True  # Activamos la bandera
        else:
            vacacion.estado = nuevo_estado

        vacacion.observaciones = request.POST.get('observaciones')
        
        autorizador_id = request.POST.get('autorizador')
        if autorizador_id:
            vacacion.autorizador_id = autorizador_id

        # 3. Configuración de Correo (Switches)
        # Los switches en HTML solo envían valor si están marcados ('on')
        vacacion.requiere_respuesta_automatica = request.POST.get('requiere_respuesta_automatica') == 'on'
        vacacion.requiere_redireccion = request.POST.get('requiere_redireccion') == 'on'

        # 4. Empleados para Redirección (Relación ManyToMany)
        if vacacion.requiere_redireccion:
            empleados_ids = request.POST.getlist('empleados_redireccion')
            vacacion.empleados_redireccion.set(empleados_ids)
        else:
            vacacion.empleados_redireccion.clear()

        # 5. Procesar Archivos
        if request.FILES.get('archivo_vacaciones'):
            vacacion.archivo_vacaciones = request.FILES.get('archivo_vacaciones')
        if request.FILES.get('archivo_roles'):
            vacacion.archivo_roles = request.FILES.get('archivo_roles')

        # Guardar cambios
        vacacion.save()

        if se_resetearon_firmas:
            # A) Cancelar tareas anteriores de esta vacación para evitar duplicados
            Tarea.objects.filter(
                objeto_id=vacacion.id, 
                tipo_objeto='vacacion', 
                estado=Tarea.EstadoTarea.PENDIENTE
            ).update(estado=Tarea.EstadoTarea.FINALIZADA)

            # B) Preparar datos para las nuevas tareas
            url_vacaciones = request.build_absolute_uri(reverse('employees:employees') + '#vacaciones-content')
            empleado_solicitante = vacacion.empleado
            jefe_asignado = vacacion.autorizador
            gerente = ConfiguracionRH.get_gerente()

            lista_fechas = sorted(vacacion.dias_seleccionados) if vacacion.dias_seleccionados else []
            f_inicio_txt = lista_fechas[0] if lista_fechas else None
            rango_dias = f"del {lista_fechas[0]} al {lista_fechas[-1]}" if len(lista_fechas) > 1 else f"el día {f_inicio_txt}"
            total = f"({len(lista_fechas)} días)" if lista_fechas else ""

            # C) Crear Tarea para Jefe
            if jefe_asignado:
                crear_tarea(
                    empleado=jefe_asignado,
                    titulo=f"REVISIÓN Vacaciones #{vacacion.id}: {empleado_solicitante.nombre}",
                    descripcion=f"La solicitud {rango_dias} {total} fue modificada y requiere nueva revisión.",
                    prioridad=Tarea.Prioridad.ALTA,
                    fecha_vencimiento=f_inicio_txt,
                    enlace=url_vacaciones,
                    objeto_id=vacacion.id,
                    tipo_objeto="vacacion"
                )

            # D) Crear Tarea para Gerente
            if gerente and gerente != jefe_asignado:
                crear_tarea(
                    empleado=gerente,
                    titulo=f"REVISIÓN Vacaciones #{vacacion.id}: {empleado_solicitante.nombre}",
                    descripcion=f"Solicitud {rango_dias} {total} modificada. Esperando validación gerencial.",
                    prioridad=Tarea.Prioridad.ALTA,
                    fecha_vencimiento=f_inicio_txt,
                    enlace=url_vacaciones,
                    objeto_id=vacacion.id,
                    tipo_objeto="vacacion"
                )

            # E) Crear Tarea para RH
            for admin_rh in Empleado.objects.filter(departamento__nombre__icontains="Recursos Humanos", estado='ACTIVO'):
                crear_tarea(
                    empleado=admin_rh,
                    titulo=f"Aviso de modificación #{vacacion.id}: {empleado_solicitante.nombre}",
                    descripcion=f"La solicitud fue editada y devuelta a revisión con el Jefe de Departamento.",
                    prioridad=Tarea.Prioridad.BAJA,
                    fecha_vencimiento=f_inicio_txt,
                    enlace=url_vacaciones,
                    objeto_id=vacacion.id,
                    tipo_objeto="vacacion"
                )

            # F) Crear Tarea para el Solicitante
            crear_tarea(
                empleado=empleado_solicitante,
                titulo=f"Cambios en tu solicitud #{vacacion.id}",
                descripcion=f"Tu solicitud {rango_dias} {total} fue actualizada y se encuentra nuevamente en revisión.",
                prioridad=Tarea.Prioridad.MEDIA,
                enlace=url_vacaciones,
                objeto_id=vacacion.id,
                tipo_objeto="vacacion"
            )
        messages.success(request, f"La solicitud de {vacacion.empleado.nombre} ha sido actualizada correctamente.")
        
    return redirect(reverse('employees:employees') + '#vacaciones-content')

@login_required
@require_POST
def AddIncapacidadView(request):
    empleado_id = request.POST.get('empleado_id')
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    try:
        fecha_inicio = request.POST.get('fecha_inicio')
        duracion = request.POST.get('duracion_dias')
        diagnostico = request.POST.get('diagnostico')
        tipo = request.POST.get('tipo')
        archivo = request.FILES.get('archivo')
        
        nueva_inca = Incapacidad(
            empleado=empleado,
            fecha_inicio=fecha_inicio,
            duracion_dias=duracion,
            diagnostico=diagnostico,
            tipo=tipo,
            archivo=archivo
        )
        nueva_inca.save()
        messages.success(request, f"Incapacidad registrada para {empleado.nombre} correctamente.")
    except Exception as e:
        messages.error(request, f"Error al registrar incapacidad: {e}")

    return redirect(reverse('employees:employees') + '#incapacidades-content')

@login_required
def EditIncapacidadView(request, incapacidad_id):
    incapacidad = get_object_or_404(Incapacidad, id=incapacidad_id)
    
    if request.method == 'POST':
        # Actualizamos los campos básicos que vienen del modal de edición
        incapacidad.fecha_inicio = request.POST.get('fecha_inicio')
        incapacidad.duracion_dias = request.POST.get('duracion_dias')
        incapacidad.diagnostico = request.POST.get('diagnostico')
        incapacidad.tipo = request.POST.get('tipo')
        
        # Si se subió un nuevo archivo, reemplazamos el anterior
        if request.FILES.get('archivo'):
            incapacidad.archivo = request.FILES.get('archivo')
            
        incapacidad.save()
        messages.success(request, "Registro de incapacidad actualizado correctamente.")
        
    # Redirigir a la pestaña de incapacidades usando el hash de la URL
    return redirect(reverse('employees:employees') + '#incapacidades-content')

@login_required
def SearchIncapacidadesView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '')
    depto_id = request.GET.get('depto_id', '')
    estacion_id = request.GET.get('estacion_id', '')

    try:
        empleado_logueado = request.user.empleado
    except:
        empleado_logueado = None

    is_admin = request.user.groups.filter(name='Administrador').exists()
    is_rh = request.user.groups.filter(name='Recursos Humanos').exists()
    es_jefe = Departamento.objects.filter(jefe=empleado_logueado).exists()

    incapacidades_qs = Incapacidad.objects.select_related('empleado', 'empleado__departamento')

    if is_admin or is_rh:
        pass
    elif es_jefe:
        deptos_del_jefe = Departamento.objects.filter(jefe=empleado_logueado)
        incapacidades_qs = incapacidades_qs.filter(empleado__departamento__in=deptos_del_jefe)
    elif empleado_logueado:
        incapacidades_qs = incapacidades_qs.filter(empleado=empleado_logueado)
    else:
        incapacidades_qs = incapacidades_qs.none()

    if query:
        incapacidades_qs = incapacidades_qs.filter(empleado__nombre__icontains=query)
    if depto_id:
        incapacidades_qs = incapacidades_qs.filter(empleado__departamento__id=depto_id)
    if estacion_id:
        incapacidades_qs = incapacidades_qs.filter(empleado__estacion_servicio__id=estacion_id)

    incapacidades_qs = incapacidades_qs.order_by('-fecha_inicio')

    paginator = Paginator(incapacidades_qs, 6)
    inca_page = paginator.get_page(page_number)

    html = render_to_string(
        '_incapacidad_cards.html',
        {
            'incapacidades_page': inca_page,
            'is_admin': is_admin,
            'is_rh': is_rh,
        },
        request=request
    )

    return JsonResponse({
        'html': html,
        'has_next': inca_page.has_next()
    })

@login_required
def EditEmpleadoView(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, request.FILES, instance=empleado, prefix="edit-empleado")
        
        if form.is_valid():
            # 1. Creamos el objeto en memoria
            empleado_editado = form.save(commit=False)
            
            # 2. Recuperamos la firma usando el nombre CON EL PREFIJO del form
            firma_b64 = request.POST.get('edit-empleado-firma_b64') 
            
            if firma_b64 and ';base64,' in firma_b64:
                try:
                    import time
                    format, imgstr = firma_b64.split(';base64,') 
                    ext = format.split('/')[-1] 
                    file_data = ContentFile(base64.b64decode(imgstr))
                    
                    timestamp = int(time.time())
                    # Nombre único para evitar caché
                    file_name = f"firma_{empleado_id}_{timestamp}.{ext}"
                    
                    # Guardamos el archivo físico
                    empleado_editado.firma_digital.save(file_name, file_data, save=False)
                    print(f"Firma guardada exitosamente para ID {empleado_id}")
                except Exception as e:
                    print(f"Error crítico procesando Base64: {e}")

            # 3. Guardamos definitivamente (UNA SOLA VEZ)
            empleado_editado.save()
            
            # 4. Guardamos relaciones ManyToMany (Grupos)
            form.save_m2m()
            
            if empleado_editado.user:
                grupos_seleccionados = form.cleaned_data.get('grupos')
                if grupos_seleccionados is not None:
                    empleado_editado.user.groups.set(grupos_seleccionados)
                
                # Comprobamos si el estado actual es ACTIVO
                es_activo = (empleado_editado.estado == Empleado.EstadoEmpleado.ACTIVO)
                
                # Si el estado del modelo User no coincide con el del Empleado, lo actualizamos
                if empleado_editado.user.is_active != es_activo:
                    empleado_editado.user.is_active = es_activo
                    empleado_editado.user.save()
            
            # Si se hizo la petición desde AJAX, respondemos con JSON para actualizar solo el modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'Empleado "{empleado.nombre}" actualizado correctamente.'})
                    
            messages.success(request, f'Empleado "{empleado.nombre}" actualizado correctamente.')
            return redirect('employees:employees')
        else:
            # Si la validación falla y es una petición AJAX, respondemos con los errores para mostrarlos en el modal sin recargar toda la página
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
            
            # Si falla la validación, imprimimos por qué en la consola de la terminal
            messages.error(request, 'Error al actualizar. Revisa los campos obligatorios.')
            return redirect('employees:employees') 

    else:
        form = EmpleadoForm(instance=empleado, prefix="edit-empleado")
    
    return render(request, '_edit_empleado_form.html', {
        'form_empleado_edit': form,
        'empleado': empleado
    })

@login_required
def AddExpedienteView(request):
    if request.method == 'POST':
        empleado_id = request.POST.get('empleado_id')
        empleado = get_object_or_404(Empleado, id=empleado_id)
        
        # Obtenemos los datos
        titulo = request.POST.get('titulo')
        tipo = request.POST.get('tipo')
        fecha_vencimiento = request.POST.get('fecha_vencimiento') or None # Manejar string vacío
        descripcion = request.POST.get('descripcion')
        firmado = request.POST.get('firmado') == 'on' # Checkbox retorna 'on' si está marcado
        archivo = request.FILES.get('archivo')
        responsables_ids = request.POST.getlist('responsables')

        # Creamos el objeto
        expediente = Expediente(
            empleado=empleado,
            usuario=request.user,
            titulo=titulo,
            tipo=tipo,
            fecha_vencimiento=fecha_vencimiento,
            descripcion=descripcion,
            firmado=firmado,
            archivo=archivo
        )
        
        # Si está firmado, podríamos poner la fecha de firma automática hoy
        if firmado:
            expediente.fecha_firma = timezone.now()

        expediente.save()
        
        if responsables_ids:
            expediente.responsables.set(responsables_ids)

        messages.success(request, f"Expediente '{titulo}' agregado correctamente.")

        url = reverse('employees:employees') 
        return redirect(f"{url}?open_modal={empleado_id}")
    
    return redirect('employees:employees')

def normalizar_texto(texto):
    """
    Transforma textos como 'Acta de nacimiento' o 'ActaDeNacimiento' 
    en 'actadenacimiento' para poder compararlos fácilmente.
    """
    if not texto:
        return ""
    # 1. Quitar acentos (NFD separa la letra del acento, luego filtramos los acentos)
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn')
    # 2. Convertir a minúsculas y dejar solo letras y números (quita espacios y guiones)
    return "".join(filter(str.isalnum, texto)).lower()

@login_required
def CargaMasivaExpedienteView(request):
    if request.method == 'POST' and 'archivos_batch' in request.FILES:
        archivos = request.FILES.getlist('archivos_batch')
        empleado_id = request.POST.get('empleado_id')
        
        temp_files = []
        for f in archivos:
            # Usamos timestamp para evitar colisiones si suben archivos con el mismo nombre
            # Reemplazamos espacios por guiones bajos de una vez para facilitar el safe_key
            nombre_limpio = f.name.replace(' ', '_')
            path = default_storage.save(
                f'temp_uploads/{timezone.now().timestamp()}_{nombre_limpio}', 
                ContentFile(f.read())
            )
            temp_files.append(path)
        
        request.session['archivos_pendientes'] = temp_files
        request.session['empleado_id_carga'] = empleado_id
        request.session.modified = True
        
        return redirect('employees:mapear_archivos')

    return redirect('employees:employees')

@login_required
def MapearArchivosView(request):
    empleado_id = request.session.get('empleado_id_carga')
    rutas_archivos = request.session.get('archivos_pendientes', [])
    
    if not empleado_id or not rutas_archivos:
        return redirect('employees:employees')

    empleado = get_object_or_404(Empleado, id=empleado_id)
    expedientes_vacios = Expediente.objects.filter(empleado=empleado, archivo='')

    if request.method == 'POST':
        conteo_exito = 0
        
        for ruta in rutas_archivos:
            nombre_temp = os.path.basename(ruta)
            # El safe_key DEBE coincidir con el del loop de abajo (GET)
            safe_key = nombre_temp.replace('.', '_').replace(' ', '_')
            
            expediente_id = request.POST.get(f'expediente_id_{safe_key}')
            firmado_check = request.POST.get(f'firmado_{safe_key}') == 'on'
            
            if not expediente_id:
                continue 

            if default_storage.exists(ruta):
                with default_storage.open(ruta) as f:
                    archivo_django = File(f)
                    # Recuperamos el nombre original quitando el timestamp
                    nombre_original = nombre_temp.split('_', 1)[-1] if '_' in nombre_temp else nombre_temp

                    try:
                        if expediente_id == "nuevo":
                            titulo_nuevo = request.POST.get(f'titulo_nuevo_{safe_key}') or nombre_original
                            exp = Expediente(
                                titulo=titulo_nuevo,
                                empleado=empleado,
                                usuario=request.user,
                                categoria=request.POST.get(f'categoria_{safe_key}', 'personal'),
                                tipo=request.POST.get(f'tipo_{safe_key}', 'otro'),
                                firmado=firmado_check,
                                estado='aprobado',
                                fecha_firma=timezone.now() if firmado_check else None
                            )
                        else:
                            exp = Expediente.objects.get(id=expediente_id)
                            exp.firmado = firmado_check
                            exp.estado = 'aprobado'
                            exp.usuario = request.user
                            if firmado_check:
                                exp.fecha_firma = timezone.now()

                        # .save() dispara expediente_directory_path y renombra el archivo
                        exp.archivo.save(nombre_original, archivo_django, save=True)
                        conteo_exito += 1
                        
                    except Exception as e:
                        print(f"Error procesando {nombre_temp}: {e}")
                
                # Borramos el temporal solo si se procesó o si queremos limpiar
                default_storage.delete(ruta)

        request.session.pop('archivos_pendientes', None)
        request.session.pop('empleado_id_carga', None)
        
        if conteo_exito > 0:
            messages.success(request, f"¡Éxito! Se integraron {conteo_exito} archivos al expediente.")
        else:
            messages.warning(request, "No se procesó ningún archivo.")

        return redirect(f"{reverse('employees:employees')}?open_modal={empleado_id}")

    # PREPARACIÓN PARA EL GET
    archivos_data = []
    for r in rutas_archivos:
        nombre = os.path.basename(r)
        archivos_data.append({
            'original': nombre.split('_', 1)[-1] if '_' in nombre else nombre,
            'safe': nombre.replace('.', '_').replace(' ', '_')
        })

    return render(request, 'mapear_archivos.html', {
        'archivos': archivos_data,
        'expedientes_vacios': expedientes_vacios,
        'empleado': empleado,
        'TIPOS_DOCUMENTO': Expediente.TIPOS_DOCUMENTO,
        'CATEGORIA_CHOICES': Expediente.CATEGORIA_CHOICES
    })

@login_required
def EditExpedienteView(request, expediente_id):
    if request.method == "POST":
        # 1. Obtenemos el expediente
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # 2. Obtenemos el ID del empleado directamente de la relación del modelo.
        # Esto es vital para saber a quién pertenece el expediente y reabrir su modal
        empleado_id = expediente.empleado.id 

        archivo_nuevo = request.FILES.get('archivo')
        
        if archivo_nuevo:
            # Asignamos el archivo
            expediente.archivo = archivo_nuevo
            
            # Opcional: Si el documento requiere firma y lo estamos subiendo, asumimos que ya viene firmado.
            if expediente.requiere_firma:
                expediente.firmado = True
                expediente.fecha_firma = timezone.now()
            
            expediente.save()
            messages.success(request, f"Archivo cargado correctamente en '{expediente.titulo}'")
        else:
            messages.error(request, "No se seleccionó ningún archivo.")

        # 3. Redirección con el truco para reabrir el modal
        base_url = reverse('employees:employees')
        return redirect(f"{base_url}?open_modal={empleado_id}")

    return redirect('employees:employees')

@login_required
def BajarExpedienteView(request, expediente_id):
    if request.method == "POST":
        expediente = get_object_or_404(Expediente, id=expediente_id)
        empleado_id = expediente.empleado.id  # Guardamos el ID antes de cualquier cambio

        if expediente.archivo:
            expediente.archivo.delete(save=False)
            expediente.archivo = None
            if expediente.requiere_firma:
                expediente.firmado = False
                expediente.fecha_firma = None
            expediente.save()
            messages.success(request, f"Documento '{expediente.titulo}' dado de baja.")
        
        # AQUÍ ESTÁ EL TRUCO:
        # Construimos la URL base y le pegamos el parámetro ?open_modal=ID
        base_url = reverse('employees:employees')
        return redirect(f"{base_url}?open_modal={empleado_id}")

    return redirect('employees:employees')

@login_required
@require_POST
def EliminarExpedienteView(request, expediente_id):
    expediente = get_object_or_404(Expediente, pk=expediente_id)
    empleado_id = expediente.empleado.id
    
    expediente.delete()

    messages.success(request, f"El requerimiento '{expediente.titulo}' fue eliminado correctamente.")
    
    base_url = redirect('employees:employees').url 
    return redirect(f"{base_url}?open_modal={empleado_id}")

@login_required
@require_POST
def UpdateFotoEmpleadoView(request, empleado_id):
    # 1. Obtenemos el empleado
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    # 2. Recuperamos el archivo del request
    nueva_foto = request.FILES.get('foto')
    
    if nueva_foto:
        try:
            # Si ya tenía una foto, opcionalmente podrías borrar la anterior físicamente
            if empleado.foto:
                empleado.foto.delete(save=False)
            
            # Asignamos y guardamos
            empleado.foto = nueva_foto
            empleado.save()
            
            messages.success(request, f'¡Foto de {empleado.nombre} actualizada correctamente!')
        except Exception as e:
            messages.error(request, f'Error al procesar la imagen: {e}')
    else:
        messages.warning(request, 'No se seleccionó ninguna imagen.')

    # 3. Regresamos a la misma página
    return redirect('employees:employees')

@login_required
@require_POST
def CargaMasivaFotosView(request):
    fotos_subidas = request.FILES.getlist('fotos_batch')
    
    if not fotos_subidas:
        messages.warning(request, "No se seleccionaron archivos.")
        return redirect('employees:employees')

    conteo_exito = 0
    usuarios_no_encontrados = []
    errores_criticos = []

    for f in fotos_subidas:
        try:
            # 1. Extraer el username (limpiando espacios y extensiones)
            nombre_usuario = os.path.splitext(f.name)[0].strip()
            
            # 2. Buscar al empleado (insensible a mayúsculas para mayor compatibilidad)
            empleado = Empleado.objects.filter(user__username__iexact=nombre_usuario).first()
            
            if empleado:
                # TRATAMOS CADA FOTO COMO UNA OPERACIÓN INDEPENDIENTE
                try:
                    # A. Actualizar foto de perfil (Sobrescribir siempre)
                    if empleado.foto:
                        empleado.foto.delete(save=False)
                    
                    empleado.foto = f
                    empleado.save()

                    # B. Crear registro en Expediente (Historial)
                    # No usamos transaction.atomic global para que si falla el expediente, 
                    # al menos la foto de perfil ya haya quedado actualizada.
                    Expediente.objects.create(
                        empleado=empleado,
                        usuario=request.user,
                        titulo=f"Fotografía de Perfil - Actualizada {timezone.now().strftime('%d/%m/%Y')}",
                        descripcion=f"Carga masiva: {f.name}",
                        categoria='personal',
                        tipo='identificacion',
                        archivo=f,
                        estado='aprobado'
                    )
                    conteo_exito += 1
                    
                except Exception as inner_e:
                    errores_criticos.append(f"Error en datos de {nombre_usuario}: {str(inner_e)}")
            else:
                usuarios_no_encontrados.append(f.name) # Guardamos el nombre del archivo fallido
                
        except Exception as e:
            errores_criticos.append(f"Error procesando archivo {f.name}: {str(e)}")

    # --- Gestión de Mensajes de Feedback ---
    if conteo_exito > 0:
        messages.success(request, f"✅ {conteo_exito} fotos actualizadas correctamente.")
    
    if usuarios_no_encontrados:
        msg_not_found = "No se encontraron empleados para estos archivos: " + ", ".join(usuarios_no_encontrados)
        messages.warning(request, msg_not_found)

    if errores_criticos:
        for error in errores_criticos:
            messages.error(request, error)

    return redirect('employees:employees')

# Solo los superusuarios pueden ejecutar esto
@user_passes_test(lambda u: u.is_superuser)
def admin_recrear_expedientes(request):
    empleados = Empleado.objects.all()
    contador = 0
    
    for emp in empleados:
        # Verificamos si NO tiene expedientes para no duplicar
        if not Expediente.objects.filter(empleado=emp).exists():
            # Llamamos a tu función del signal manualmente
            # Le pasamos created=True para que entre en el bloque if de tu lógica
            crear_documentos_base(sender=Empleado, instance=emp, created=True)
            contador += 1
            
    messages.success(request, f"¡Éxito! Se generaron expedientes para {contador} empleados.")
    return redirect('admin:employees_empleado_changelist')