from django.db import models

class Curso(models.Model):
    titulo = models.CharField(max_length=200, help_text="Título oficial del curso")
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción detallada del curso")
    
    fecha = models.DateField(
        null=True, 
        blank=True, 
        help_text="Fecha programada para el curso (YYYY-MM-DD)"
    )
    
    horario = models.TimeField(
        null=True, 
        blank=True, 
        help_text="Hora de inicio del curso (HH:MM)"
    )
    
    duracion_horas = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        null=True, 
        blank=True, 
        help_text="Duración total del curso en horas (Ej. 2.5)"
    )
    
    plataforma = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Plataforma o lugar (Ej. Zoom, Teams, Sala de Juntas 1)"
    )

    link = models.URLField(
        max_length=255, 
        blank=True,
        null=True,
        help_text="Enlace a la sesión (Zoom, Teams) o a los materiales del curso"
    )

    es_general = models.BooleanField(
        default=False,
        verbose_name="Curso General",
        help_text="Marcar si este curso es para TODOS los departamentos."
    )

    imagen = models.ImageField(
        upload_to='cursos_portadas/', 
        blank=True,                   # Permite que el campo esté vacío (opcional)
        null=True,                    
        help_text="Imagen de portada para el curso (Si se tiene)"
    )
    
    departamentos_destinados = models.ManyToManyField(
        'employees.Departamento',
        related_name="cursos_disponibles",
        blank=True,
        help_text="Departamentos que pueden ver y tomar este curso"
    )
    
    inscritos = models.ManyToManyField(
        'employees.Empleado',
        related_name="cursos_inscritos",
        blank=True,
        help_text="Empleados que están inscritos o han tomado este curso"
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
    
    image = models.ImageField(upload_to='slides/', verbose_name="Imagen")
    alt_text = models.CharField(max_length=150, verbose_name="Texto Alternativo (Alt)")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    is_active = models.BooleanField(default=True, verbose_name="Está activo")

    class Meta:
        verbose_name = "Slide"
        verbose_name_plural = "Slides"
        ordering = ['order']

    def __str__(self):
        return self.title
    
class TipoDocumento(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Tipo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documento"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Documento(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        OBSOLETO = 'obsoleto', 'Obsoleto'
        BORRADOR = 'borrador', 'Borrador'

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
        default=False,
        verbose_name="Formato General",
        help_text="Marcar si este formato es para TODOS los departamentos."
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