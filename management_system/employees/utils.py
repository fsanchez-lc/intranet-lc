import threading
from django.core.mail import send_mail
from django.conf import settings
from .models import Tarea
# 1. Creamos una función separada solo para enviar el correo
def enviar_correo_tarea_async(empleado_email, empleado_nombre, titulo, descripcion, prioridad, fecha_vencimiento, enlace):
    asunto = f"Nueva Tarea: {titulo}"
    mensaje = f"""Hola {empleado_nombre},

    Se te ha asignado una nueva tarea en el sistema.

    📋 DETALLES DE LA TAREA:
    ----------------------------------------
    - Título: {titulo}
    - Descripción: {descripcion if descripcion else 'Sin descripción detallada.'}
    - Prioridad: {prioridad}
    - Fecha de vencimiento: {fecha_vencimiento if fecha_vencimiento else 'Sin fecha definida'}

    Para revisar esta tarea y gestionarla, por favor ingresa al siguiente enlace:
    {enlace if enlace else 'Inicia sesión en el sistema para revisar tu panel de tareas.'}

    Saludos,
    El Sistema de Recursos Humanos.
    """
    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[empleado_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error enviando correo de tarea a {empleado_email}: {e}")


def crear_tarea(empleado, titulo, **kwargs):
    if not empleado or not titulo:
        return None

    descripcion = kwargs.get('descripcion', '')
    prioridad = kwargs.get('prioridad', Tarea.Prioridad.MEDIA)
    estado = kwargs.get('estado', Tarea.EstadoTarea.PENDIENTE)
    enlace = kwargs.get('enlace', '')
    fecha_vencimiento = kwargs.get('fecha_vencimiento', None)

    # Creamos la tarea en la base de datos (Esto es súper rápido)
    tarea = Tarea.objects.create(
        empleado=empleado,
        titulo=titulo,
        descripcion=descripcion,
        prioridad=prioridad,
        estado=estado,
        enlace=enlace,
        fecha_vencimiento=fecha_vencimiento,
        objeto_id=kwargs.get('objeto_id', None),
        tipo_objeto=kwargs.get('tipo_objeto', None),
        fecha_completado=kwargs.get('fecha_completado', None)
    )
    
    # 2. Despachamos el envío del correo en un hilo paralelo
    if empleado.email:
        hilo_correo = threading.Thread(
            target=enviar_correo_tarea_async,
            args=(empleado.email, empleado.nombre, titulo, descripcion, prioridad, fecha_vencimiento, enlace)
        )
        hilo_correo.start() # Inicia el envío y continúa el código de abajo inmediatamente

    return tarea