from django.contrib import admin
from .models import Curso, Slide, TipoDocumento, Documento, VideoCurso, InscripcionCurso

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    
    list_editable = ('order', 'is_active')
    
    list_filter = ('is_active',)
    
    search_fields = ('title', 'description')

class InscripcionCursoInline(admin.TabularInline):
    model = InscripcionCurso 
    
    fields = (
        'empleado', 'estado', 'fecha_finalizacion', 'calificacion', 'certificado'
    )
    
    extra = 0
    
    autocomplete_fields = ['empleado'] 
    
    readonly_fields = ('fecha_inscripcion',)

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha', 'plataforma', 'duracion_horas', 'modalidad' ,'estado')
    list_filter = ('estado','plataforma', 'modalidad', 'departamentos_destinados')

    list_editable = ('fecha', 'estado',)
    search_fields = ('titulo', 'descripcion', 'plataforma')
    
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

@admin.register(InscripcionCurso)
class InscripcionCursoAdmin(admin.ModelAdmin):
    list_display = ('curso', 'empleado', 'estado', 'fecha_finalizacion', 'calificacion')
    list_filter = ('estado', 'fecha_finalizacion')
    # Permite buscar inscripciones por nombre del curso o empleado
    search_fields = ('curso__titulo', 'empleado__nombre', 'empleado__email')