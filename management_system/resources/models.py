from django.db import models
from django.utils import timezone
from datetime import timedelta
import os
from django.core.files.storage import FileSystemStorage

# 1. Almacenamiento personalizado: Sobreescribe archivos si tienen el mismo nombre
class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            os.remove(os.path.join(self.location, name))
        return name
    
def slide_upload_path(instance, filename):
    # Si por alguna razón no hay mes/año, usamos el actual
    anio = instance.anio or timezone.now().year
    mes = instance.mes or timezone.now().month
    # Retorna la ruta limpia
    return f"slides/{anio}/{mes}/{filename}"

class Curso(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        INACTIVO = 'inactivo', 'Inactivo'
        FINALIZADO = 'finalizado', 'Finalizado'
        
    class Modalidad(models.TextChoices):
        AUTOINSCRIPCION = 'auto', 'Autoinscripción'
        SOLICITUD = 'solicitud', 'Pedir inscribirse'

    titulo = models.CharField(
        max_length=200, 
        help_text="Título oficial del curso"
    )
    
    descripcion = models.TextField(
        blank=True, null=True, 
        help_text="Descripción detallada del curso", 
        verbose_name="Descripción"
    )
    
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.ACTIVO,
        verbose_name="Estado",
        help_text="Define si el curso está activo o inactivo."
    )

    modalidad = models.CharField(
        max_length=10,
        choices=Modalidad.choices,
        default=Modalidad.AUTOINSCRIPCION,
        verbose_name="Modalidad de Inscripción",
        help_text="Define si el usuario puede inscribirse directamente o debe solicitarlo."
    )
    
    fecha = models.DateField(
        help_text="Fecha programada para el curso (YYYY-MM-DD)"
    )
    
    horario = models.TimeField(
        help_text="Hora de inicio del curso (HH:MM)"
    )
    
    duracion_horas = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        verbose_name="Duración (horas)",
        null=True, 
        blank=True, 
        help_text="Duración total del curso en horas (Ej. 2.5)"
    )
    
    plataforma = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="Plataforma o lugar (Ej. Zoom, Teams, Sala de Juntas 1)"
    )

    link = models.URLField(
        max_length=255,
        blank=True,
        null=True, 
        help_text="Enlace a la sesión (Zoom, Teams) o a los materiales del curso"
    )

    es_general = models.BooleanField(
        default=True,
        verbose_name="Curso General",
        help_text="Desmarcar si este curso NO es para TODOS los departamentos."
    )

    departamentos_destinados = models.ManyToManyField(
        'employees.Departamento',
        related_name="cursos_disponibles",
        blank=True,
        help_text="Departamentos que pueden ver y tomar este curso"
    )

    imagen = models.ImageField(
        upload_to='cursos_portadas/',
        blank=True,
        null=True,
        help_text="Imagen de portada para el curso (Si se tiene)"
    )
    
    inscritos = models.ManyToManyField(
        'employees.Empleado',
        related_name="cursos_inscritos",
        blank=True,
        help_text="Empleados que están inscritos o han tomado este curso"
    )

    participantes = models.ManyToManyField(
        'employees.Empleado',
        through='InscripcionCurso',
        related_name="cursos_historial_detallado", # Cambiado para evitar conflicto
        blank=True,
        verbose_name="Historial de Participación Detallado"
    )

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['titulo']
        
    def __str__(self):
        return self.titulo
    
class Slide(models.Model):
    title = models.CharField(max_length=100, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción", blank=True, null=True)
    
    # 3. Campos nuevos para control de carpetas y almacenamiento
    mes = models.IntegerField(null=True, blank=True, verbose_name="Mes")
    anio = models.IntegerField(null=True, blank=True, verbose_name="Año")
    
    image = models.ImageField(
        upload_to=slide_upload_path, 
        storage=OverwriteStorage(), 
        verbose_name="Imagen"
    )
    
    alt_text = models.CharField(
        max_length=150, 
        verbose_name="Texto Alternativo (Alt)",
        blank=True, 
        null=True,  
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    is_active = models.BooleanField(default=True, verbose_name="Está activo")

    class Meta:
        verbose_name = "Slide"
        verbose_name_plural = "Slides"
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.mes}/{self.anio})"
    
class TipoDocumento(models.Model):
    class Categoria(models.TextChoices):
        INTERNO = 'interno', 'Documentación Interna'
        EXTERNO = 'externo', 'Marco Normativo / Externo'
    
    class SubCategoria(models.TextChoices):
        PROCEDIMIENTO = 'procedimiento', 'Procedimiento / Manual'
        FORMATO = 'formato', 'Formato / Plantilla'
        OTRO = 'otro', 'Otro'

    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Tipo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    categoria = models.CharField(
        max_length=20, 
        choices=Categoria.choices, 
        default=Categoria.INTERNO
    )

    sub_categoria = models.CharField(
        max_length=20,
        choices=SubCategoria.choices,
        default=SubCategoria.FORMATO,
        verbose_name="Subcategoría"
    )

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documento"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
class Area(models.Model):
    """📍 Nivel 1: Representa las grandes divisiones (ej. Operaciones, Administración)"""
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Área")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ['nombre']

    def __str__(self):
        return f"📍 {self.nombre}"

class Proceso(models.Model):
    """⚙️ Nivel 2: Conjunto de actividades (ej. Reclutamiento, Ventas, Mantenimiento)"""
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name="procesos", null=True, blank=True) # Añade null=True
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Proceso")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Proceso"
        verbose_name_plural = "Procesos"
        ordering = ['nombre']
        unique_together = ('area', 'nombre') # Evita procesos duplicados en la misma área

    def __str__(self):
        return f"⚙️ {self.nombre} ({self.area.nombre})"
    
class Procedimiento(models.Model):
    """📑 Nivel 3: El 'paso a paso' específico (ej. Solicitud de Vacaciones, Arqueo de Caja)"""
    proceso = models.ForeignKey(Proceso, on_delete=models.CASCADE, related_name="procedimientos", null=True, blank=True)
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Procedimiento")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    
    # Quitamos la relación ManyToMany con Departamento para que sea puramente jerárquico
    # pero si quieres filtros por departamento en RRHH, lo manejamos vía Documento.

    class Meta:
        verbose_name = "Procedimiento"
        verbose_name_plural = "Procedimientos"
        ordering = ['nombre']

    def __str__(self):
        return f"📑 {self.nombre}"
    
class Documento(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        OBSOLETO = 'obsoleto', 'Obsoleto'

    nombre = models.CharField(
        max_length=200, 
        help_text="Nombre oficial del formato o plantilla"
    )

    descripcion = models.TextField(
        blank=True, 
        null=True, 
        help_text="Propósito del formato y cuándo debe usarse."
    )

    codigo_documento = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True, 
        help_text="Código único de control (ej. RRHH-FOR-001)"
    )

    palabras_clave = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Etiquetas separadas por comas para facilitar la búsqueda (ej. vacaciones, permiso, solicitud)"
    )

    tipo_documento = models.ForeignKey(
        TipoDocumento, 
        on_delete=models.PROTECT,
        related_name="documentos",
        help_text="Clasificación: Formato, Plantilla, Manual, etc."
    )

    procedimiento = models.ForeignKey(
        Procedimiento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos",
        help_text="¿A qué flujo de trabajo pertenece? (Ej: Onboarding, Solicitud de Vacaciones)"
    )

    estado = models.CharField(
        max_length=10, 
        choices=Estado.choices, 
        default=Estado.ACTIVO, 
        help_text="Estado del ciclo de vida del documento."
    )
    
    archivo = models.FileField(
        upload_to='formatos/%Y/%m/', # Guarda en /media/formatos/AÑO/MES/
        blank=True, 
        null=True, 
        help_text="Subir el archivo (PDF, DOCX, XLSX, etc.)"
    )
    
    enlace_externo = models.URLField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Opcional: Si el formato está en Google Doc, SharePoint, etc."
    )

    es_general = models.BooleanField(
        default=True,
        verbose_name="Formato General",
        help_text="Desmarcar si este formato NO es para TODOS los departamentos."
    )

    departamentos_destinados = models.ManyToManyField(
        'employees.Departamento', 
        related_name="documentos_disponibles", 
        blank=True,
        help_text="Departamentos que pueden ver y usar este formato (si no es 'general')."
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Última Modificación")
    
    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        # Ordenar por nombre
        ordering = ['nombre']
        
    def __str__(self):
        # Un __str__ descriptivo para el admin
        if self.codigo_documento:
            return f"[{self.codigo_documento}] {self.nombre}"
        return f"{self.nombre}" 
    
class TematicaVideo(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Temática")
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Temática de Video"
        verbose_name_plural = "Temáticas de Videos"

    def __str__(self):
        return self.nombre

class VideoCurso(models.Model):
    @property
    def es_reciente(self):
        # Retorna True si se subió en los últimos 4 días
        # Usa 'created_at' o el campo de fecha que tengas de registro
        if self.fecha_registro:
            return self.fecha_registro >= timezone.now() - timedelta(days=4)
        return False
    
    ESTADO_CHOICES = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    )

    tematica = models.ForeignKey(
        TematicaVideo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="videos",
        verbose_name="Temática"
    )

    curso = models.ForeignKey(
        Curso, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="videos_grabados",
        verbose_name="Curso al que pertenece"
    )

    es_general = models.BooleanField(
        default=True,
        verbose_name="Formato General",
        help_text="Desmarcar si este formato NO es para TODOS los departamentos."
    )
    
    # TÍTULO: El título del video
    titulo = models.CharField(
        max_length=255, 
        verbose_name="Título del Video"
    ) 
    
    # URL: El enlace normal de YouTube o Drive
    video_url = models.URLField(
        max_length=500, 
        verbose_name="URL del Video",
        help_text="Pega el enlace normal de YouTube (watch?v=...) o Google Drive (file/d/.../view)."
    )
    
    # PONENTE: El "autor"
    ponente = models.CharField(
        max_length=150, 
        verbose_name="Ponente o Instructor", 
        blank=True # Es opcional
    )
    
    # FECHA: La fecha de la grabación
    fecha_grabacion = models.DateField(
        verbose_name="Fecha de Grabación",
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        default=timezone.now, 
        verbose_name="Fecha de Registro/Subida"
    )
    
    # ESTADO: Para activar o desactivar
    estado = models.CharField(
        max_length=10, 
        choices=ESTADO_CHOICES, 
        default='activo', 
        verbose_name="Estado"
    )

    departamentos_destinados = models.ManyToManyField(
        'employees.Departamento', 
        related_name="videos_disponibles", 
        blank=True,
        help_text="Departamentos que pueden ver este video (si no es 'general')."
    )

    # --- MÉTODO PARA CONVERTIR URL ---
    @property
    def get_embed_url(self):
        
        # 1. Lógica para YouTube
        if "youtube.com/watch?v=" in self.video_url:
            try:
                # Extrae el ID: '...watch?v=VIDEO_ID&...' -> 'VIDEO_ID'
                video_id = self.video_url.split('v=')[1].split('&')[0]
                return f"https://www.youtube.com/embed/{video_id}"
            except Exception:
                return None # URL mal formada

        # 2. Lógica para YouTube Corto (youtu.be)
        if "youtu.be/" in self.video_url:
            try:
                # Extrae el ID: '...youtu.be/VIDEO_ID?...' -> 'VIDEO_ID'
                video_id = self.video_url.split('youtu.be/')[1].split('?')[0]
                return f"https://www.youtube.com/embed/{video_id}"
            except Exception:
                return None # URL mal formada

        # 3. Lógica para Google Drive
        if "drive.google.com/file/d/" in self.video_url:
            try:
                # Extrae el ID: '.../d/FILE_ID/view...' -> 'FILE_ID'
                file_id = self.video_url.split('/d/')[1].split('/')[0]
                return f"https://drive.google.com/file/d/{file_id}/preview"
            except Exception:
                return None # URL mal formada
        
        # 4. Fallback: Si ya es un enlace embed, simplemente devuélvelo
        if "/embed/" in self.video_url or "/preview" in self.video_url:
            return self.video_url

        # 5. Si no se reconoce, no se puede mostrar
        return None

    class Meta:
        verbose_name = "Video de Curso"
        verbose_name_plural = "Videoteca de Cursos"
        ordering = ['-fecha_registro']

    def __str__(self):
        return self.titulo
    
class InscripcionCurso(models.Model):
    class EstadoInscripcion(models.TextChoices):
        INSCRITO = 'INSCRITO', 'Inscrito'
        COMPLETADO = 'COMPLETADO', 'Completado'
        APROBADO = 'APROBADO', 'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'
        DADO_DE_BAJA = 'DADO DE BAJA', 'Dado de Baja'

    curso = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE, 
        related_name="historial_participantes",
        verbose_name="Curso"
    )
    
    empleado = models.ForeignKey(
        'employees.Empleado', 
        on_delete=models.CASCADE, 
        related_name="historial_cursos",
        verbose_name="Empleado"
    )

    estado = models.CharField(
        max_length=15,
        choices=EstadoInscripcion.choices,
        default=EstadoInscripcion.INSCRITO,
        verbose_name="Estado de Participación"
    )
    
    fecha_finalizacion = models.DateField(
        null=True, blank=True,
        verbose_name="Fecha de Finalización"
    )
    
    calificacion = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name="Calificación (0-100)"
    )
    
    certificado = models.FileField(
        upload_to='certificados_cursos/%Y/',
        null=True, blank=True,
        verbose_name="Certificado/Diploma"
    )
    
    fecha_inscripcion = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de Inscripción"
    )

    class Meta:
        verbose_name = "Inscripción y Historial"
        verbose_name_plural = "Inscripciones y Historial"
        ordering = ['-fecha_finalizacion']
        # Esto asegura que no se pueda tener dos registros idénticos (mismo curso, mismo empleado).
        unique_together = ('curso', 'empleado') 
        
    def __str__(self):
        return f"{self.empleado.nombre} - {self.curso.titulo} ({self.estado})"