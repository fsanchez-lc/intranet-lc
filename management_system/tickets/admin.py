from django.contrib import admin
from .models import Ticket, Comentario

class ComentarioInline(admin.TabularInline):
    """
    Permite ver y añadir comentarios directamente desde la vista de un Ticket.
    """
    model = Comentario
    extra = 1  # Muestra un campo vacío para añadir un nuevo comentario por defecto.
    readonly_fields = ('fecha_creacion',)
    fields = ('autor', 'texto', 'tipo', 'visibilidad', 'fecha_creacion')
    autocomplete_fields = ['autor'] # Mejora la selección del autor

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """
    Configuración para el modelo Ticket en el panel de administración.
    """
    list_display = (
        'id', 
        'titulo', 
        'estado', 
        'prioridad', 
        'creado_por', 
        'estacion_servicio', 
        'fecha_creacion',
        'fecha_cerrado'
    )
    list_filter = ('estado', 'prioridad', 'estacion_servicio')
    search_fields = ('titulo', 'descripcion', 'creado_por__nombre', 'estacion_servicio__nombre')
    
    readonly_fields = ('fecha_creacion', 'ultima_actualizacion', 'fecha_cerrado')

    fieldsets = (
        (None, {
            'fields': ('titulo', 'descripcion')
        }),
        ('Detalles y Estado', {
            'fields': ('estado', 'prioridad', 'estacion_servicio')
        }),
        ('Información de Creación', {
            'fields': ('creado_por', 'fecha_creacion', 'ultima_actualizacion', 'fecha_cerrado')
        }),
    )
    
    # Incrusta la gestión de comentarios dentro del formulario del ticket.
    inlines = [ComentarioInline]
    
    list_per_page = 25

@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    """
    Vista de administración para ver y gestionar todos los comentarios de forma centralizada.
    """
    list_display = ('autor', 'ticket', 'tipo', 'visibilidad', 'fecha_creacion')
    list_filter = ('tipo', 'visibilidad', 'autor')
    search_fields = ('texto', 'autor__nombre', 'ticket__titulo')
    autocomplete_fields = ['ticket', 'autor']

