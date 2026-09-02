from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
# Importa tus modelos (ajusta la ruta según el nombre de tu app)
from .models import Ticket
from django.http import HttpRequest
from tickets.forms import TicketForm

#ALMACENAR NOTIFICACION PARA USUARIO POSTERIOR A LA CREACION DE TICKET (TICKET CREADO CORRECTAMENTE)
from django.contrib import messages
#REDIRECCIONAR A OTRA URL
from django.shortcuts import redirect

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

    #CREAMOS UNA INSTANCIA DE TICKETFORM, CUANDO SE CREE UN TICKET, SE RELLENARAN LOS CAMPOS
    ticket_form = TicketForm()

    # 4. Empaquetamos todo en el contexto y lo enviamos al template
    context = {
        'lista_de_tickets': lista_de_tickets,
        'tickets_abiertos': tickets_abiertos,
        'tickets_proceso': tickets_proceso,
        'tickets_alta': tickets_alta,
        'tickets_cerrados': tickets_cerrados,
        #AGREGAMOS EL TICKETFORM AL CONTEXT 
        'ticket_form' : ticket_form,
    }

    return render(request, 'tickets.html', context)        


##PRIMERO VALIDAMOS QUE EL REQUEST SEA POST
# AL SER POST, ALAMACENAMOS REQUEST EN UNA VARIABLE
# VALIDAMOS QUE SEA VALIDO
# SI VALIDO ALMACENAMOS EL EMPLEADO QUE MANDO EL REQUEST
# 
# SI ES NULO DEVOLVEMOS ERROR
# 
# SI NO ES NULO, SALVAMOS EL TICKET EN UNA VARIABLE, 
# 
# ASIGNAMOS CREADO POR Y ESTACION DE SERVICIO 
# 
# SALVAMOS, DEVOLVEMOS MENSAJE 
# 
# REDIRECCIONAMOS##


#VALIDACION DE USUARIO PARA LA CREACION
@login_required
def CreateTicketView(request : HttpRequest):

    #VALIDAMOS QUE SEA POST, EN CASO CONTRARIO REDIRECCIONA 
    if request.method != "POST":
        return redirect("tickets:tickets_url")

#ALMACENAMOS EL TicketForm CON LOS DATOS DEL REQUEST ENVIADOS DESDE EL FORMULARIO VALIDADOS CON EL FORMS.PY
    ticket_form = TicketForm(request.POST)


##EN CASO DE ERROR, REDIRECCIONAMOS Y AVISAMOS AL USUARIO
# VALIDA QUE EXISTA EL TITULO
# NO EXCEDA LA LONGITUD
# EXISTA  UNA DESCRIPCION
# ETC.
# ##
    if not ticket_form.is_valid():
        messages.error(request, "No fue posible crear el ticket. Revisa los datos ingresados.")
        return redirect("tickets:tickets_url")

#ALMACENAMOS EL EMPLEADO PARA VALIDACIONES
    empleado_actual = getattr(request.user, "empleado", None)

#VALIDAMOS QUE EL USUARIO QUE REALIZA EL REQUEST TENGA EMPLEADO ASOCIADO, SINO REDIRECCIONAMOS Y AVISAMOS
    if empleado_actual is None:
        messages.error(request, "Debes tener un empleado asociado para generar un ticket.")
        return redirect("tickets:tickets_url")

#CREAMOS EL Ticket(), PERO AUN NO HACEMOS EL COMMIT A LA DB
    ticket = ticket_form.save(commit=False)

#COMPLETAMOS LOS CAMPOS QUE VIENEN DESDE EL EMPLEADO Y GUARDAMOS
    ticket.creado_por = empleado_actual
    ticket.estacion_servicio = empleado_actual.estacion_servicio

#AHORA SI, CON LOS CAMPOS COMPLETOS, SALVAMOS EN LA DB
    ticket.save()

#AVISAMOS AL USUARIO QUE SE CREO CORRECTAMENTE EL TICKET Y REDIRECCIONAMOS
    messages.success(request, "El ticket fue creado correctamente")
    return redirect("tickets:tickets_url")
