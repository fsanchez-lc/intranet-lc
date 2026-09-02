import openpyxl
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.urls import path
from openpyxl.worksheet.datavalidation import DataValidation

# Importaciones de tus modelos
from .models import Empleado, Departamento, Expediente, Tarea, Vacacion, Incapacidad, ConfiguracionRH
from service_stations.models import ServiceStation 

# Importación de Import/Export
from import_export.admin import ImportExportModelAdmin
from .employee_resources import EmpleadoResource

# --- FUNCIÓN PARA GENERAR LA PLANTILLA EXCEL ---
def descargar_plantilla_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plantilla Importación"

    # 1. Encabezados exactos según tu imagen
    headers = [
        'id', 'numero_empleado', 'nombre', 'email', 'sexo', 'departamento', 
        'posicion', 'estacion_servicio', 'fecha_ingreso', 
        'fecha_nacimiento', 'telefono_emergencia',
    ]
    ws.append(headers)

    # 2. Obtener datos reales para las listas desplegables
    deptos = [d.nombre for d in Departamento.objects.all()]
    estaciones = [s.nombre for s in ServiceStation.objects.all()]
    sexos = ['M', 'F', 'N']

    # Validación Sexo (Ahora es la Columna E porque movimos numero_empleado)
    dv_sexo = DataValidation(type="list", formula1=f'"{",".join(sexos)}"', allow_blank=True)
    ws.add_data_validation(dv_sexo)
    dv_sexo.add("E2:E500")

    # Validación Departamento (Ahora es la Columna F)
    if deptos:
        dv_depto = DataValidation(type="list", formula1=f'"{",".join(deptos)}"', allow_blank=True)
        ws.add_data_validation(dv_depto)
        dv_depto.add("F2:F500")

    # Validación Estación de Servicio (Ahora es la Columna H)
    if estaciones:
        dv_estacion = DataValidation(type="list", formula1=f'"{",".join(estaciones)}"', allow_blank=True)
        ws.add_data_validation(dv_estacion)
        dv_estacion.add("H2:H500")

    # Formato de celdas para fechas (Ahora son Columnas I y J)
    for row in ws.iter_rows(min_row=2, max_row=500, min_col=9, max_col=10):
        for cell in row:
            cell.number_format = 'yyyy-mm-dd'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=plantilla_empleados.xlsx'
    wb.save(response)
    return response

class EmpleadoAdminForm(forms.ModelForm):
    # Definimos las opciones que aparecerán en el admin
    OPCIONES_PERMISOS = [
        ('ver-dashboards', 'Ver Dashboards'),
        ('vacaciones', '🏖️ Ver Vacaciones'),
        ('tareas', '✅ Ver Tareas'),
        ('nominas', '💰 Ver Nóminas/Salarios'),
    ]

    permisos_secciones = forms.MultipleChoiceField(
        choices=OPCIONES_PERMISOS,
        widget=forms.CheckboxSelectMultiple, # Esto crea los cuadritos para marcar
        required=False,
        label="Secciones Desbloqueadas"
    )

    class Meta:
        model = Empleado
        fields = '__all__'

    # Cargamos los datos guardados en el JSONField al formulario
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.permisos_secciones:
            self.fields['permisos_secciones'].initial = self.instance.permisos_secciones

# --- INLINES ---
class VacacionInline(admin.TabularInline):
    model = Vacacion
    fk_name = 'empleado'
    extra = 0
    fields = ('dias_seleccionados', 'autorizador', 'gerente_autorizador', 'estado')
    classes = ('collapse',)
    show_change_link = True

class TareaInline(admin.TabularInline):
    model = Tarea
    extra = 1
    classes = ('collapse',) # Opcional: para que se pueda contraer

class ExpedienteInline(admin.TabularInline):
    model = Expediente
    extra = 0
    # Agregamos extension_plantilla para ver/editar rápido el tipo de machote
    fields = ('titulo', 'categoria', 'tipo', 'archivo', 'extension_plantilla', 'firmado', 'estado')
    readonly_fields = ('fecha_creacion',)
    classes = ('collapse',)
    can_delete = True
    show_change_link = True

class IncapacidadInline(admin.TabularInline):
    model = Incapacidad
    fk_name = 'empleado'
    extra = 0
    fields = ('fecha_inicio', 'duracion_dias', 'archivo', 'fecha_registro')
    readonly_fields = ('fecha_registro',)
    classes = ('collapse',)
    show_change_link = True

# --- ADMIN RH ---
@admin.register(ConfiguracionRH)
class ConfiguracionRHAdmin(admin.ModelAdmin):
    list_display = ['gerente_general']

class VacacionAdminForm(forms.ModelForm):
    # Creamos un campo virtual más amigable
    dias_ingresados = forms.CharField(
        label="Días específicos",
        required=False,
        help_text="Ingresa las fechas (AAAA-MM-DD) separadas por comas. Ej: 2024-12-24, 2024-12-25",
        widget=forms.Textarea(attrs={
            'rows': 3, 
            'placeholder': '2024-12-24, 2024-12-25'
        })
    )

    class Meta:
        model = Vacacion
        fields = '__all__'
        # Excluimos el campo crudo original
        exclude = ['dias_seleccionados']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si ya hay fechas guardadas, las cargamos separadas por coma
        if self.instance and self.instance.pk and self.instance.dias_seleccionados:
            if isinstance(self.instance.dias_seleccionados, list):
                self.fields['dias_ingresados'].initial = ", ".join(self.instance.dias_seleccionados)

    def clean_dias_ingresados(self):
        # Recibimos el texto, lo separamos por comas y limpiamos espacios
        data = self.cleaned_data.get('dias_ingresados', '')
        if not data.strip():
            return []
        
        fechas = [f.strip() for f in data.split(',') if f.strip()]
        return fechas

    def save(self, commit=True):
        # Guardamos la lista de Python resultante de vuelta al campo JSON real
        instance = super().save(commit=False)
        instance.dias_seleccionados = self.cleaned_data.get('dias_ingresados', [])
        if commit:
            instance.save()
            self.save_m2m() # Importante si tienes campos ManyToMany
        return instance

# --- ADMIN VACACION ---
@admin.register(Vacacion)
class VacacionAdmin(admin.ModelAdmin):
    form = VacacionAdminForm
    list_display = (
        'empleado',
        'dias_solicitados_lista',
        'total_dias_visual',
        'autorizador',
        'firma_jefe',
        'gerente_autorizador',
        'firma_gerente',
        'estado_badge', 
        'ver_formatos'
    )

    list_filter = ('estado', 'requiere_respuesta_automatica', 'requiere_redireccion', 'autorizador_firmado', 'gerente_firmado', 'empleado__departamento')
    search_fields = ('empleado__nombre', 'autorizador__nombre', 'gerente_autorizador__nombre')
    autocomplete_fields = ['empleado', 'autorizador', 'gerente_autorizador']
    filter_horizontal = ('empleados_redireccion',)

    fieldsets = (
        ('Información de la Solicitud', {
            'fields': ('empleado', 'dias_ingresados', 'estado')
        }),
        ('Autorizaciones', {
            'fields': (
                'autorizador', ('autorizador_firmado', 'autorizador_fecha_firma'),
                'gerente_autorizador', ('gerente_firmado', 'gerente_fecha_firma'),
            )
        }),
        ('Configuración de Correo (Ausencia)', {
            'fields': (
                'requiere_respuesta_automatica', 
                'requiere_redireccion', 
                'empleados_redireccion'
            ),
            'description': 'Ajustes para el mensaje de fuera de la oficina y delegación de correos.'
        }),
        ('Documentación Adjunta', {
            'fields': ('archivo_vacaciones', 'archivo_roles', 'observaciones')
        }),
    )

    # --- Columnas de firma ---
    @admin.display(description='✍️ Jefe', boolean=True)
    def firma_jefe(self, obj):
        return obj.autorizador_firmado

    @admin.display(description='✍️ Gerente', boolean=True)
    def firma_gerente(self, obj):
        return obj.gerente_firmado
    
    @admin.display(description='Días Solicitados')
    def dias_solicitados_lista(self, obj):
        if obj.dias_seleccionados:
            fechas = sorted(obj.dias_seleccionados)
            if len(fechas) <= 3:
                return ", ".join(fechas)
            return f"{fechas[0]} ... {fechas[-1]} ({len(fechas)} días)"
        return "-"
    
    @admin.display(description='Días')
    def total_dias_visual(self, obj):
        # Usamos el property del modelo
        return format_html('<b>{} días</b>', obj.total_dias)

    @admin.display(description='Documentos')
    def ver_formatos(self, obj):
        html = ""
        if obj.archivo_vacaciones:
            html += f'<a href="{obj.archivo_vacaciones.url}" target="_blank" title="Vacaciones">📄 VAC</a> '
        if obj.archivo_roles:
            html += f'<a href="{obj.archivo_roles.url}" target="_blank" title="Roles" style="color: purple;">📄 ROL</a>'
        return format_html(html) if html else "-"

    @admin.display(description='Estado')
    def estado_badge(self, obj):
        colores = {
            'PENDIENTE': '#FF8F00',
            'APROBADO': '#2E7D32',
            'RECHAZADO': '#C62828',
            'DISFRUTADO': '#1565C0',
        }
        color = colores.get(obj.estado, '#000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_estado_display().upper()
        )

# --- ADMIN DEPARTAMENTO ---
@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'id')
    search_fields = ('nombre',)
    ordering = ('nombre',)

# --- ADMIN EXPEDIENTE ---
@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = (
        'titulo', 
        'empleado_link',    # Nombre del empleado clickeable
        'categoria_visual', # Con colores (Laboral/Personal)
        'tipo', 
        'ext_plantilla',    # Muestra si es PDF/DOCX
        'ver_archivo',      # Icono de descarga
        'firmado_icon',     # Icono visual
        'estado_badge',     # Estado con colores
        'fecha_vencimiento'
    )
    
    list_filter = (
        'categoria',
        'tipo', 
        'estado',
        'firmado', 
        'extension_plantilla', # Nuevo filtro
        'empleado__departamento',
        'fecha_creacion'
    )
    
    search_fields = (
        'titulo', 
        'empleado__nombre', 
        'empleado__email', 
        'descripcion'
    )
    
    autocomplete_fields = ['empleado', 'usuario']
    
    date_hierarchy = 'fecha_creacion'

    # Organización en pestañas/grupos (Fieldsets)
    fieldsets = (
        ('Información del Documento', {
            'fields': ('titulo', 'descripcion', 'empleado', 'usuario')
        }),
        ('Clasificación y Plantilla', {
            'fields': (
                ('categoria', 'tipo'),
                'extension_plantilla' # Aquí defines si el machote es pdf, docx, etc.
            ),
            'description': 'Define "docx" o "xlsx" si el formato base en static no es un PDF.'
        }),
        ('Estado y Archivo Real', {
            'fields': ('archivo', 'estado', 'requiere_firma', 'firmado', 'fecha_firma')
        }),
        ('Fechas', {
            'fields': ('fecha_vencimiento', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    # --- Decoradores para la lista ---

    @admin.display(description='Empleado', ordering='empleado')
    def empleado_link(self, obj):
        return obj.empleado.nombre

    @admin.display(description='Firmado', boolean=True)
    def firmado_icon(self, obj):
        return obj.firmado

    @admin.display(description='Archivo')
    def ver_archivo(self, obj):
        if obj.archivo:
            return format_html(
                '<a href="{}" target="_blank" style="color:green; font-weight:bold;">'
                '<i class="bi bi-download"></i> Descargar</a>', 
                obj.archivo.url
            )
        return format_html('<span style="color: #ccc;">Pendiente</span>')

    @admin.display(description='Ext.', ordering='extension_plantilla')
    def ext_plantilla(self, obj):
        return obj.extension_plantilla.upper()

    @admin.display(description='Categoría', ordering='categoria')
    def categoria_visual(self, obj):
        # Azul para laboral, Verde para personal
        color = '#1565C0' if obj.categoria == 'laboral' else '#2E7D32'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', 
            color, obj.get_categoria_display()
        )

    @admin.display(description='Estado', ordering='estado')
    def estado_badge(self, obj):
        colores = {
            'pendiente': '#FF8F00', # Naranja
            'aprobado': '#2E7D32',  # Verde oscuro
            'rechazado': '#C62828', # Rojo
            'archivado': '#757575'  # Gris
        }
        color = colores.get(obj.estado, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 6px; border-radius: 4px; font-size: 11px;">{}</span>', 
            color, obj.get_estado_display().upper()
        )

# --- ADMIN EMPLEADO ---
@admin.register(Empleado)
class EmpleadoAdmin(ImportExportModelAdmin):
    
    resource_class = EmpleadoResource
    form = EmpleadoAdminForm
    list_display = (
        'ver_foto',
        'nombre', 
        'email', 
        'numero_empleado',
        'departamento', 
        'estacion_servicio', 
        'ver_firma',
        'ver_permisos_activos',
        'estado_visual',
        'fecha_ingreso',
    )
    
    list_display_links = ('ver_foto', 'nombre')
    
    search_fields = (
        'nombre', 
        'email', 
        'departamento__nombre', 
        'estacion_servicio__nombre',
        'posicion',
        'telefono',
        'numero_empleado'
    )
    
    list_filter = (
        'estado', 
        'departamento', 
        'estacion_servicio',
        'sexo',
        'fecha_ingreso',
        'grupos'
    )
    
    filter_horizontal = ('grupos',)
    list_select_related = ('departamento', 'estacion_servicio', 'user')
    inlines = [ExpedienteInline, TareaInline, VacacionInline, IncapacidadInline]

    readonly_fields = ('ver_foto',)

    fieldsets = (
        ('Información Personal', {
            'fields': (
                ('ver_foto', 'foto'),
                'numero_empleado',
                ('nombre', 'sexo'),
                ('email', 'telefono'),
                ('fecha_nacimiento', 'telefono_emergencia'),
                'firma_digital'
            )
        }),
        ('Información Laboral', {
            'fields': (
                ('departamento', 'posicion'),
                'estacion_servicio',
                ('fecha_ingreso', 'fecha_finalizacion'),
                'estado'
            )
        }),
        ('Permisos de Visualización', {
            'fields': ('permisos_secciones',),
            'description': 'Marque las secciones que este empleado podrá ver en su panel personal.'
        }),
        ('Acceso al Sistema', {
            'fields': ('user', 'grupos'),
            'description': 'Vinculación con el usuario de Django y permisos.'
        }),
    )

    # --- Decoradores ---
    @admin.display(description='Permisos Activos')
    def ver_permisos_activos(self, obj):
        if not obj.permisos_secciones:
            return format_html('<span style="color: #999;">Abierto (Todo)</span>')
        tags = "".join([f'<span style="background:#eee; padding:2px 5px; margin:2px; border-radius:3px; font-size:10px;">{p}</span>' for p in obj.permisos_secciones])
        return format_html(tags)

    @admin.display(description='Estado', ordering='estado')
    def estado_visual(self, obj):
        color = 'green' if obj.estado == 'ACTIVO' else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', 
            color, obj.get_estado_display()
        )

    @admin.display(description='Firma Digital')
    def ver_firma(self, obj):
        if obj.firma_digital:
            return format_html(
                '<img src="{}" style="height: 30px; border:1px solid #ccc; border-radius:3px;" />', 
                obj.firma_digital.url
            )
        return "-"
    @admin.display(description='Foto')
    def ver_foto(self, obj):
        if obj.foto: # Asegúrate de que el campo en tu modelo se llame 'foto'
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 1px solid #ddd;" />', 
                obj.foto.url
            )
        return format_html('<i class="bi bi-person-circle" style="font-size: 24px; color: #ccc;"></i>')

    change_list_template = "admin/employees/empleado_change_list.html"

    # 2. Registramos la URL para que el botón sepa a qué función llamar
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('descargar-plantilla/', self.admin_site.admin_view(descargar_plantilla_excel), name='descargar-plantilla'),
        ]
        return my_urls + urls
    
