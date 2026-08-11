from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from employees.models import Empleado
from django.contrib.auth import get_user_model
from resources.models import Slide
from resources.forms import SlideForm
from employees.models import Tarea
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from .models import LogConsultaReporte

User = get_user_model()

@login_required
def DashboardView(request):
    empleado = getattr(request.user, 'empleado', None)
    conteo_empleados = Empleado.objects.all().count()
    conteo_usuarios = User.objects.all().count()
    slides_activos = Slide.objects.filter(is_active=True)
    
    tareas = Tarea.objects.filter(
        empleado=empleado
    ).filter(
        Q(estado=Tarea.EstadoTarea.PENDIENTE) | 
        Q(estado=Tarea.EstadoTarea.EN_PROGRESO) |
        Q(estado=Tarea.EstadoTarea.COMPLETADA)

    ).order_by('-prioridad')
    
    form_slide = SlideForm(prefix='create_slide')
    form_with_errors = None

    is_admin = request.user.groups.filter(name='Administrador').exists()
    is_rh = request.user.groups.filter(name='Recursos Humanos').exists()
    is_gerente = request.user.groups.filter(name='Gerente').exists()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'slide':
            form_slide = SlideForm(request.POST, request.FILES, prefix='create_slide')
            if form_slide.is_valid():
                form_slide.save()
                messages.success(request, '¡Nuevo slide añadido correctamente!')
                return redirect('resources:resources')
            else:
                messages.error(request, 'Error al añadir el slide. Revisa los campos.')
                form_with_errors = 'slide'
        else:
            messages.error(request, 'Error desconocido al enviar el formulario.')
            form_slide = SlideForm(prefix='create_slide')
    else:
        form_slide = SlideForm(prefix='create_slide')


    context = {
        'slides': slides_activos,
        'empleado': empleado,
        'title': 'Panel de Control',
        'total_empleados': conteo_empleados,
        'total_usuarios': conteo_usuarios,
        'form_with_errors': form_with_errors,

        'is_admin': is_admin,
        'is_rh': is_rh,
        'is_gerente': is_gerente,
        'tareas': tareas
    }
    return render(request, 'home.html', context)

@login_required
def CambiarEstadoTareaView(request, tarea_id):
    if request.method == 'POST':
        tarea = Tarea.objects.get(id=tarea_id)
        nuevo_estado = request.POST.get('estado')
        
        if tarea.empleado.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'No autorizado'}, status=403)
        
        tarea.estado = nuevo_estado
        if nuevo_estado == 'COMPLETADA':
            tarea.fecha_completado = timezone.now()
        else:
            tarea.fecha_completado = None
            
        tarea.save()
        return JsonResponse({'status': 'ok'})

@login_required
def ValidarAccesoReporteView(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        password_ingresada = data.get('password')

        origen = data.get('origen', 'Desconocido')
        # Definir contraseña (puedes usar variables de entorno para más seguridad)
        PASSWORD_CORRECTA = "Lopez2026" 
        
        # Obtener IP del usuario
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

        if password_ingresada == PASSWORD_CORRECTA:
            # Registrar éxito
            LogConsultaReporte.objects.create(
                usuario=request.user, 
                accion=f"Acceso Exitoso a Reportes desde {origen}",
                ip_address=ip
            )
            return JsonResponse({'status': 'ok'})
        else:
            # Registrar intento fallido
            LogConsultaReporte.objects.create(
                usuario=request.user, 
                accion=f"Intento fallido desde {origen} (Clave: {password_ingresada})",
                ip_address=ip
            )
            return JsonResponse({'status': 'error'}, status=403)
        
@login_required
def DashboardsVariosView(request, template_name='dashboard-1.html'):
    is_admin = request.user.groups.filter(name='Administrador').exists()
    is_rh = request.user.groups.filter(name='Recursos Humanos').exists()
    is_gerente = request.user.groups.filter(name='Gerente').exists()
    
    # SOLUCIÓN: Usar getattr para que devuelva None si no existe la relación
    empleado = getattr(request.user, 'empleado', None) 

    context = {
        'title': 'Dashboard 1',
        'is_admin': is_admin,
        'is_rh': is_rh,
        'is_gerente': is_gerente,
        'empleado': empleado,
    }
    return render(request, template_name, context)