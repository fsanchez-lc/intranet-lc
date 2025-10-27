from django.shortcuts import render, redirect, get_object_or_404 
from .models import Equipo, TipoEquipo, EstadoEquipo 
from employees.models import Empleado
from service_stations.models import ServiceStation
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required

@login_required
def EquipmentView(request):
    tipos = TipoEquipo.objects.all().order_by('nombre')
    estados = EstadoEquipo.objects.all().order_by('nombre')
    empleados = Empleado.objects.filter(estado=Empleado.EstadoEmpleado.ACTIVO).order_by('nombre')
    estaciones = ServiceStation.objects.all().order_by('nombre')
        
    equipos_registrados = Equipo.objects.filter(estado_registro=Equipo.EstadoRegistro.ACTIVO)

    context = {
        'tipos_de_equipo': tipos,
        'estados_de_equipo': estados,
        'empleados': empleados,
        'estaciones_de_servicio': estaciones,
        'lista_de_equipos': equipos_registrados,
    }
    return render(request, 'equipment.html', context)

@login_required
def TypeEquipmentView(request):
    return render(request, 'type_equipment.html', {})

@login_required
def CreateEquipmentView(request):
    # Solo procesamos si el método es POST
    if request.method == 'POST':
        # 1. Recuperar los datos del formulario
        nombre = request.POST.get('nombre')
        marca = request.POST.get('marca')
        modelo = request.POST.get('modelo')
        numero_serie = request.POST.get('numero_serie')
        
        # 2. Recuperar IDs de las llaves foráneas
        tipo_equipo_id = request.POST.get('tipo_equipo')
        estado_id = request.POST.get('estado')
        asignado_a_id = request.POST.get('asignado_a')
        estacion_id = request.POST.get('estacion_servicio')

        # 3. Recuperar fechas
        fecha_compra = request.POST.get('fecha_compra')
        vencimiento_garantia = request.POST.get('vencimiento_garantia')

        # 4. Crear el nuevo objeto Equipo
        nuevo_equipo = Equipo(
            nombre=nombre,
            marca=marca,
            modelo=modelo,
            numero_serie=numero_serie,
        )

        # 5. Asignar llaves foráneas (si se seleccionaron)
        if tipo_equipo_id:
            nuevo_equipo.tipo_equipo_id = tipo_equipo_id
        if estado_id:
            nuevo_equipo.estado_id = estado_id
        if asignado_a_id:
            nuevo_equipo.asignado_a_id = asignado_a_id
        if estacion_id:
            nuevo_equipo.estacion_servicio_id = estacion_id
        
        # 6. Asignar fechas (si se ingresaron)
        if fecha_compra:
            nuevo_equipo.fecha_compra = fecha_compra
        if vencimiento_garantia:
            nuevo_equipo.vencimiento_garantia = vencimiento_garantia

        # 7. Guardar en la base de datos
        try:
            nuevo_equipo.save()
            messages.success(request, '¡Equipo añadido exitosamente!')
        except IntegrityError:
            messages.error(request, 'Error: Ya existe un equipo con ese Número de Serie.')

        # 8. Redirigir a la lista de equipos para ver el nuevo registro
        return redirect('lista_equipos')

    # Si no es POST, redirigir a la lista (o manejar como un error)
    return redirect('lista_equipos')

@login_required
def EditEquipmentView(request, pk):
    # 1. Busca el equipo por su ID (pk). Si no lo encuentra, muestra un error 404.
    equipo_a_editar = get_object_or_404(Equipo, pk=pk)

    if request.method == 'POST':
        # 2. Actualiza los campos del objeto existente con los datos del formulario
        equipo_a_editar.nombre = request.POST.get('nombre')
        equipo_a_editar.marca = request.POST.get('marca')
        equipo_a_editar.modelo = request.POST.get('modelo')
        equipo_a_editar.numero_serie = request.POST.get('numero_serie')
        
        # Asigna llaves foráneas
        equipo_a_editar.tipo_equipo_id = request.POST.get('tipo_equipo')
        equipo_a_editar.estado_id = request.POST.get('estado')
        equipo_a_editar.asignado_a_id = request.POST.get('asignado_a')
        equipo_a_editar.estacion_servicio_id = request.POST.get('estacion_servicio')

        # Asigna fechas, manejando el caso de que vengan vacías
        fecha_compra = request.POST.get('fecha_compra')
        equipo_a_editar.fecha_compra = fecha_compra if fecha_compra else None
        
        vencimiento_garantia = request.POST.get('vencimiento_garantia')
        equipo_a_editar.vencimiento_garantia = vencimiento_garantia if vencimiento_garantia else None

        # 3. Guarda los cambios en la base de datos
        try:
            equipo_a_editar.save()
            messages.info(request, '¡Cambios guardados exitosamente!')

        except IntegrityError:
            messages.error(request, 'Ya existe otro equipo con el mismo Número de Serie. Verifique la información')
        
        # 4. Redirige de vuelta a la lista de equipos
        return redirect('lista_equipos')

    return redirect('lista_equipos')

@login_required
def DeactivateEquipmentView(request, pk):
    equipo_a_desactivar = get_object_or_404(Equipo, pk=pk)

    if request.method == 'POST':
        equipo_a_desactivar.estado_registro = Equipo.EstadoRegistro.INACTIVO
        equipo_a_desactivar.save()        
        # --- AÑADIR MENSAJE DE ERROR (para el color rojo) ---
        messages.warning(request, 'El equipo ha sido eliminado.')
        
        return redirect('lista_equipos')
    # Si se accede por GET, simplemente redirigir (o mostrar una página de confirmación)
    return redirect('lista_equipos')