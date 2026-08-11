from django.contrib import admin
from .models import Guia, Paso

class PasoInline(admin.TabularInline): 
    model = Paso
    extra = 1  
    fields = ['orden', 'instruccion', 'imagen']

@admin.register(Guia)
class GuiaAdmin(admin.ModelAdmin):
    # 1. Agregamos 'sistema' al list_display para verlo en la tabla
    list_display = ('orden', 'sistema', 'titulo', 'descripcion_corta')
    
    # 2. Hacemos que 'orden' y 'sistema' sean editables desde la lista
    list_editable = ('orden', 'sistema')
    
    # 3. Agregamos un filtro lateral para separar por SLAM o SICA
    list_filter = ('sistema',)
    
    # 4. Buscador para encontrar guías por título
    search_fields = ('titulo', 'descripcion')
    
    list_display_links = ('titulo',)
    inlines = [PasoInline]

    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + "..." if obj.descripcion else ""
    descripcion_corta.short_description = 'Descripción'