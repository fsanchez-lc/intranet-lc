from django.contrib import admin
from .models import Curso, Slide, TipoDocumento, Documento, VideoCurso

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    # Campos que se mostrarán en la lista del admin
    list_display = ('title', 'order', 'is_active')
    
    # Campos que se pueden editar directamente desde la lista
    list_editable = ('order', 'is_active')
    
    # Filtros que aparecerán a la derecha
    list_filter = ('is_active',)
    
    # Un buscador
    search_fields = ('title', 'description')

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha', 'plataforma', 'duracion_horas', 'modalidad' ,'estado')
    list_filter = ('estado','plataforma', 'modalidad', 'departamentos_destinados')

    list_editable = ('fecha', 'estado',)
    search_fields = ('titulo', 'descripcion', 'plataforma')
    
    # Para campos ManyToMany, 'filter_horizontal' es más amigable
    filter_horizontal = ('departamentos_destinados', 'inscritos')

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(VideoCurso)
class VideoCursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'ponente', 'fecha_grabacion', 'estado')
    list_filter = ('estado', 'curso', 'ponente')
    search_fields = ('titulo', 'ponente', 'curso__titulo')
    filter_horizontal = ('departamentos_destinados',)

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 
        'codigo_documento', 
        'tipo_documento', 
        'estado', 
        'es_general', 
        'fecha_modificacion'
    )

    list_filter = ('estado', 'tipo_documento', 'es_general', 'departamentos_destinados')
    
    search_fields = ('nombre', 'codigo_documento', 'descripcion', 'palabras_clave')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('nombre', 'codigo_documento', 'tipo_documento', 'palabras_clave')
        }),
        ('Detalles y Archivo', {
            'fields': ('descripcion', 'estado', 'archivo', 'enlace_externo')
        }),
        ('Audiencia (Destinatarios)', {
            'description': "Usa 'Formato General' para todos, o selecciona departamentos específicos.",
            'fields': ('es_general', 'departamentos_destinados')
        }),
        ('Metadatos (Automático)', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ('departamentos_destinados',)
    
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    
    list_per_page = 25