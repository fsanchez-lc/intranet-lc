from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
# Importa tus modelos (ajusta la ruta según el nombre de tu app)
from .models import Ticket 

@login_required
def TicketsView(request):
    # 1. Obtenemos al empleado asociado al usuario actual
    try:
        empleado_actual = request.user.empleado
    except AttributeError:
        # Por si un admin entra sin tener un perfil de Empleado creado
        empleado_actual = None

    # 2. Construimos la consulta principal de tickets
    if empleado_actual:
        # Esta es la magia de Q(). Trae los tickets si se cumple CUALQUIERA de estas 3 reglas:
        lista_de_tickets = Ticket.objects.filter(
            Q(creado_por=empleado_actual) |                     # Regla 1: Yo lo creé
            Q(asignado_a=empleado_actual) |                     # Regla 2: Me lo asignaron para resolverlo
            Q(departamento_destino__jefe=empleado_actual)       # Regla 3: Soy el Jefe de ese departamento
        ).distinct().order_by('-fecha_creacion') 
        # distinct() evita duplicados por si alguien es jefe y creador al mismo tiempo
        
    elif request.user.is_superuser:
        # Si es un superusuario sin perfil de empleado, lo dejamos ver todo
        lista_de_tickets = Ticket.objects.all().order_by('-fecha_creacion')
    else:
        # Si no cumple nada, mandamos una lista vacía
        lista_de_tickets = Ticket.objects.none()

    # 3. Calculamos las métricas para las 4 tarjetas superiores del template
    # Reutilizamos 'lista_de_tickets' para que las métricas solo cuenten los tickets que el usuario SÍ puede ver
    tickets_abiertos = lista_de_tickets.filter(estado=Ticket.Estado.ABIERTO).count()
    
    # Para "En Proceso" podemos sumar los ASIGNADOS y los EN_PROCESO
    tickets_proceso = lista_de_tickets.filter(estado__in=[Ticket.Estado.ASIGNADO, Ticket.Estado.EN_PROCESO]).count()
    
    # Urgencias: Tickets con prioridad ALTA que NO estén cerrados
    tickets_alta = lista_de_tickets.filter(prioridad=Ticket.Prioridad.ALTA).exclude(estado=Ticket.Estado.CERRADO).count()
    
    tickets_cerrados = lista_de_tickets.filter(estado=Ticket.Estado.CERRADO).count()

    # 4. Empaquetamos todo en el contexto y lo enviamos al template
    context = {
        'lista_de_tickets': lista_de_tickets,
        'tickets_abiertos': tickets_abiertos,
        'tickets_proceso': tickets_proceso,
        'tickets_alta': tickets_alta,
        'tickets_cerrados': tickets_cerrados,
    }

    return render(request, 'tickets.html', context)