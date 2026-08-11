from django.contrib import admin
from .models import LogConsultaReporte

@admin.register(LogConsultaReporte)
class LogConsultaReporteAdmin(admin.ModelAdmin):
    # Columnas que se verán en la lista principal
    list_display = ('usuario', 'accion', 'ip_address', 'fecha_hora')
    
    # Filtros laterales para búsqueda rápida
    list_filter = ('accion', 'fecha_hora', 'usuario')
    
    # Buscador por nombre de usuario e IP
    search_fields = ('usuario__username', 'ip_address', 'accion')
    
    # Ordenar por fecha (lo más reciente arriba)
    ordering = ('-fecha_hora',)
    
    # Hacer que los campos sean de solo lectura para evitar alteraciones en la auditoría
    readonly_fields = ('usuario', 'accion', 'ip_address', 'fecha_hora')

    def has_add_permission(self, request):
        # Evita que se creen logs manualmente desde el admin
        return False