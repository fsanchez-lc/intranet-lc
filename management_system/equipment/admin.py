from django.contrib import admin
from .models import Equipo, TipoEquipo, EstadoEquipo

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'numero_serie', 'tipo_equipo', 'estado', 'asignado_a')
    list_filter = ('tipo_equipo', 'estado', 'fecha_compra')
    search_fields = ('nombre', 'numero_serie', 'marca', 'modelo')

@admin.register(TipoEquipo)
class TipoEquipoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)

@admin.register(EstadoEquipo)
class EstadoEquipoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)

