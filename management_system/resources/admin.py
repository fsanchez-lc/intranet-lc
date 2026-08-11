from django.contrib import admin
from .models import Curso, Slide, TipoDocumento, Documento, VideoCurso, InscripcionCurso, Procedimiento, TematicaVideo, Area, Proceso

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

@admin.register(TematicaVideo)
class TematicaVideoAdmin(admin.ModelAdmin):
    # Columnas que se verán en la tabla principal
    list_display = ('nombre', 'get_video_count')
    # Permite buscar por nombre
    search_fields = ('nombre',)
    
    # Función extra para mostrar cuántos videos tiene cada tema
    def get_video_count(self, obj):
        return obj.videos.count()
    
    get_video_count.short_description = 'Total de Videos'

class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 0
    fields = ('nombre', 'tipo_documento', 'estado')
    readonly_fields = ('nombre', 'tipo_documento', 'estado') # Solo lectura para no saturar

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Proceso)
class ProcesoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'area')
    list_filter = ('area',)

@admin.register(Procedimiento)
class ProcedimientoAdmin(admin.ModelAdmin):
    # Asegúrate de que estas columnas existan en el modelo
    list_display = ('nombre', 'proceso', 'get_area')
    list_filter = ('proceso__area', 'proceso')
    search_fields = ('nombre',)

    def get_area(self, obj):
        # Validamos: Si el objeto tiene proceso y ese proceso tiene área...
        if obj.proceso and obj.proceso.area:
            return obj.proceso.area.nombre
        return "⚠️ Sin Área asignada" # Mensaje amigable en lugar de un error
    
    get_area.short_description = 'Área'

@admin.register(VideoCurso)
class VideoCursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'tematica', 'ponente', 'fecha_grabacion', 'fecha_registro', 'estado', 'check_reciente')
    list_filter = ('estado', 'curso', 'ponente')
    list_editable = ('estado', 'fecha_grabacion')
    search_fields = ('titulo', 'ponente', 'curso__titulo')
    filter_horizontal = ('departamentos_destinados',)
    ields = ('titulo', 'video_url', 'ponente', 'fecha_grabacion', 'fecha_registro', 'tematica', 'curso', 'estado', 'es_general', 'departamentos_destinados')

    # Creamos un método para que se vea bonito en el admin (con iconos)
    @admin.display(description='¿Es Reciente?', boolean=False)
    def check_reciente(self, obj):
        from django.utils.html import format_html
        if obj.es_reciente: # Llama a la @property del modelo
            return format_html('<span style="color: #198754; font-weight: bold;">🟢 NUEVO</span>')
        return format_html('<span style="color: #6c757d;">Antiguo</span>')

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'sub_categoria', 'categoria', 'get_document_count')
    list_editable = ('sub_categoria',)
    list_filter = ('categoria', 'sub_categoria')
    search_fields = ('nombre',)

    def get_document_count(self, obj):
        return obj.documentos.count()
    
    get_document_count.short_description = 'Documentos vinculados'

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 
        'codigo_documento', 
        'tipo_documento', 
        'get_subcategoria',
        'procedimiento',
        'estado', 
        'es_general', 
        'fecha_modificacion'
    )

    list_filter = ('estado', 'tipo_documento__sub_categoria', 'tipo_documento', 'procedimiento', 'es_general', 'departamentos_destinados')
    
    search_fields = ('nombre', 'codigo_documento', 'descripcion', 'palabras_clave')

    # Método para mostrar la subcategoría en la lista (ya que es FK)
    def get_subcategoria(self, obj):
        return obj.tipo_documento.get_sub_categoria_display()
    
    get_subcategoria.short_description = 'Subcategoría'
    get_subcategoria.admin_order_field = 'tipo_documento__sub_categoria'
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('nombre', 'codigo_documento', 'tipo_documento', 'procedimiento', 'palabras_clave')
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