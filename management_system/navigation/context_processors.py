from employees.models import Tarea

def contador_tareas_global(request):
    """
    Este código se ejecutará en CADA carga de página del sistema.
    """
    count = 0
    
    # 1. Verificamos que el usuario esté logueado
    if request.user.is_authenticated:
        # 2. Verificamos que tenga un perfil de empleado asociado
        if hasattr(request.user, 'empleado'):
            empleado_actual = request.user.empleado
            
            # 3. Contamos las tareas
            count = Tarea.objects.filter(
                empleado=empleado_actual, 
                estado__in=['PENDIENTE', 'EN_PROGRESO'] 
            ).count()

    # 4. Devolvemos el diccionario que se inyectará en el HTML
    return {
        'tareas_pendientes_count': count,
        }