from django.contrib import admin
from .models import TipoEquipo, EstadoEquipo, Equipo, AsignacionEquipo

# (Si ya tenías registrados TipoEquipo y EstadoEquipo, déjalos como estaban)

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    # 1. Cambiamos 'estado' por 'estado_fisico' y 'estatus'
    # 2. Reemplazamos 'asignado_a' por una función personalizada 'asignado_actualmente'
    list_display = ['nombre', 'marca', 'numero_serie', 'estado_fisico', 'estatus', 'asignado_actualmente']
    
    # Cambiamos 'estado' por los nuevos campos
    list_filter = ['estatus', 'estado_fisico', 'tipo_equipo'] 
    
    search_fields = ['nombre', 'numero_serie', 'marca', 'modelo']

    # Función personalizada para mostrar a quién está asignado el equipo en el panel
    @admin.display(description='Asignado a')
    def asignado_actualmente(self, obj):
        # Busca si hay una asignación activa (donde no lo han devuelto)
        asignacion_activa = obj.asignaciones.filter(fecha_devolucion__isnull=True).first()
        if asignacion_activa:
            return asignacion_activa.empleado.nombre
        return "Nadie (En Bodega/Fijo)"

# Y aprovechamos para registrar el nuevo modelo de historial de asignaciones
@admin.register(AsignacionEquipo)
class AsignacionEquipoAdmin(admin.ModelAdmin):
    list_display = ['equipo', 'empleado', 'fecha_asignacion', 'fecha_devolucion', 'esta_activo']
    list_filter = ['fecha_asignacion']
    search_fields = ['equipo__nombre', 'empleado__nombre']