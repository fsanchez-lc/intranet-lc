from django.contrib import admin
from .models import ServiceStation

@admin.register(ServiceStation)
class ServiceStationAdmin(admin.ModelAdmin):
    """
    Configuración para el modelo ServiceStation en el panel de administración.
    """
    # Asegúrate de que los campos aquí coincidan con los del modelo.
    # 'responsable' se usa directamente porque ahora es un CharField.
    list_display = ('nombre', 'responsable', 'estado', 'ubicacion')
    
    # La búsqueda ahora se hace directamente sobre el campo de texto 'responsable'.
    search_fields = ('nombre', 'ubicacion', 'responsable')
    
    list_filter = ('estado',)
    list_per_page = 20

