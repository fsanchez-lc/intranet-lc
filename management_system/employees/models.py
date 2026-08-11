from django.db import models
from django.contrib.auth.models import Group, User
from django.conf import settings
from django.utils.text import slugify
from datetime import datetime, date
import os
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.files.storage import FileSystemStorage

class ConfiguracionRH(models.Model):
    gerente_general = models.ForeignKey(
        'Empleado',
        on_delete=models.PROTECT,
        related_name='es_gerente_general',
        verbose_name='Gerente General'
    )
    
    class Meta:
        verbose_name = 'Configuración de RH'
        verbose_name_plural = 'Configuración de RH'
    
    def __str__(self):
        return f"Gerente: {self.gerente_general.nombre}"
    
    @classmethod
    def get_gerente(cls):
        config = cls.objects.first()
        return config.gerente_general if config else None

class SeccionPermiso(models.Model):
    nombre = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="Nombre técnico sin espacios"
    )
    etiqueta = models.CharField(
        max_length=100, 
        help_text="Nombre que verá el Administrador (Ej: Ver Vacaciones)"
    )

    def __str__(self):
        return self.etiqueta

    class Meta:
        verbose_name = "Configuración de Sección"
        verbose_name_plural = "Configuraciones de Secciones"

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    jefe = models.ManyToManyField(
        'Empleado', 
        blank=True, 
        related_name='departamentos_bajo_mando',
        verbose_name="Jefe de Departamento"
    )

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"

import os

def expediente_directory_path(instance, filename):
    # 1. Extraer la extensión
    ext = filename.split('.')[-1]
    
    # 2. Obtener el título y nombre del empleado
    # Mantenemos los espacios tal cual están en la base de datos
    titulo_doc = instance.titulo
    nombre_empleado = instance.empleado.nombre

    # 4. Construir el nombre final con espacios
    nombre_archivo_final = f"{titulo_doc}_{nombre_empleado}.{ext}"
    
    # 5. La ruta de la carpeta
    ruta_carpeta = f"expedientes/{nombre_empleado}"
    
    # Unimos todo
    return os.path.join(ruta_carpeta, nombre_archivo_final)

class MyStorage(FileSystemStorage):
    def get_valid_name(self, name):
        # Esto le dice a Django: "No toques el nombre, confío en lo que mando"
        return name
    
class Expediente(models.Model):
    # Campos básicos
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    requiere_firma = models.BooleanField(
        default=False,
        verbose_name="¿Requiere firma?",
        help_text="Indica si este documento necesita ser firmado digitalmente por el empleado."
    )

    responsables = models.ManyToManyField(
        'employees.Empleado', 
        blank=True, 
        related_name='expedientes_responsable',
        verbose_name="Responsables",
        help_text="Personas encargadas de dar seguimiento a este expediente."
    )
    
    CATEGORIA_CHOICES = [
        ('personal', 'Documentación Personal'),
        ('laboral', 'Documentación Laboral'),
    ]

    extension_plantilla = models.CharField(
        max_length=5, 
        default='pdf', 
        help_text="Extensión del archivo en static (pdf, docx, xlsx)"
    )
    
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='personal')

    firmado = models.BooleanField(
        default=False, 
        help_text="Marcar si el expediente ya cuenta con las firmas necesarias."
    )
    
    archivo = models.FileField(
        upload_to=expediente_directory_path,
        storage=MyStorage(),
        blank=True, 
        null=True
    )

    empleado = models.ForeignKey(
        'employees.Empleado', 
        on_delete=models.CASCADE, 
        related_name='expedientes',
        help_text="Empleado al que pertenece este expediente o documento."
    )

    # 3. Relación con Usuario: ¿De quién es este expediente?
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expedientes',
        blank=True, null=True,
        help_text="Usuario al que pertenece este expediente."
    )

    # 4. Fechas de control (Auditoría)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # 5. Fecha de la firma
    # A veces es mejor saber CUÁNDO se firmó, no solo SI se firmó.
    fecha_firma = models.DateTimeField(
        blank=True, 
        null=True, 
        help_text="Fecha y hora en que se realizó la firma."
    )
    
    fecha_vencimiento = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Fecha de Vencimiento",
        help_text="Fecha en la que expira este documento (ej. fin de contrato)."
    )

    # 6. Estado del Expediente (Flujo de trabajo)
    ESTADOS = [
        ('pendiente', 'Pendiente de Revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('archivado', 'Archivado'),
    ]
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS, 
        default='pendiente'
    )

    TIPOS_DOCUMENTO = [
        ('contrato', 'Contrato'),
        ('identificacion', 'Identificación'),
        ('certificacion', 'Certificación'),
        ('comprobante', 'Comprobante'),
        ('constancia', 'Constancia'),
        ('documento', 'Documento'),
        ('convenio', 'Convenio'),
        ('responsiva', 'Responsiva'),
        ('acta', 'Acta'),
        ('baja', 'Documento de Baja'),
        ('otro', 'Otro'),
    ]
    tipo = models.CharField(
        max_length=50, 
        choices=TIPOS_DOCUMENTO, 
        default='otro',
        verbose_name="Tipo de Documento"
    )

    def __str__(self):
        return f"{self.titulo} ({'Firmado' if self.firmado else 'No firmado'})"
    
    class Meta:
        verbose_name = "Expediente"
        verbose_name_plural = "Expedientes"

class Empleado(models.Model):

    class GeneroChoices(models.TextChoices):
        FEMENINO = 'F', 'Femenino'
        MASCULINO = 'M', 'Masculino' 
        NO_ESPECIFICADO = 'N', 'Prefiero no especificar'

    numero_empleado = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Número de Empleado / ID",
        help_text="Número o clave única de identificación del empleado (Ej. 001234 o EMP-001)."
    )
    
    sexo = models.CharField(
        max_length=1,
        choices=GeneroChoices.choices,
        default=GeneroChoices.NO_ESPECIFICADO,
        verbose_name="Sexo",
        help_text="Sexo del empleado."
    )

    user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL,
        related_name="empleado",
        null=True, 
        blank=True,
        verbose_name="Usuario del Sistema"
    )

    class EstadoEmpleado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'

    nombre = models.CharField(
        max_length=255, 
        help_text="Nombre completo del empleado.",
        verbose_name="Nombre completo",
    )

    apodo = models.CharField(
        max_length=50, 
        blank=True, 
        null=True
    )

    fecha_nacimiento = models.DateField(
        verbose_name="Fecha de Nacimiento",
        help_text="Fecha de nacimiento para cálculos de edad y beneficios."
    )
    
    fecha_ingreso = models.DateField(
        verbose_name="Fecha de Ingreso",
        help_text="Fecha en la que el empleado inició labores. Crucial para antigüedad."
    )
    
    fecha_finalizacion = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Finalización/Baja",
        help_text="Fecha de finalización de labores (si aplica)."
    )
    
    telefono_emergencia = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Teléfono de Emergencia",
        help_text="Número de contacto en caso de emergencia."
    )

    email = models.EmailField(unique=True, help_text="Correo electrónico del empleado.")
    
    telefono = models.CharField(
        max_length=20, blank=True,
        verbose_name="Teléfono",
    )

    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    posicion = models.CharField(
        max_length=100, 
        help_text="Ej: Coordinadora de RRHH",
        verbose_name="Puesto de Trabajo",
    )

    estacion_servicio = models.ForeignKey(
        'service_stations.ServiceStation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Centro de Trabajo",
        related_name="empleados",
        help_text="Centro de trabajo a la que está asignado el empleado."
    )

    grupos = models.ManyToManyField(
        Group,
        blank=True,
        related_name="empleados",
        verbose_name="Tipo de Usuario",
        help_text="Tipo de usuario al que pertenece el empleado. El administrador define sus permisos."
    )

    estado = models.CharField(
        max_length=10,
        choices=EstadoEmpleado.choices,
        default=EstadoEmpleado.ACTIVO
    )

    foto = models.ImageField(
        upload_to='fotos_empleados/',
        null=True,
        blank=True,
        verbose_name="Foto de Perfil",
        help_text="Sube la foto del rostro del empleado para su identificación."
    )

    firma_digital = models.ImageField(
        upload_to='firmas_empleados/',
        null=True,
        blank=True,
        help_text="Sube una imagen de la firma digital del empleado."
    )
    
    permisos_secciones = models.JSONField(
        default=list, 
        blank=True, 
        verbose_name="Permisos de Secciones",
        help_text="Lista de secciones a las que el empleado tiene acceso."
    )

    def tiene_permiso(self, nombre_seccion):
        if not self.permisos_secciones:
            return True # O False, dependiendo de si quieres que por defecto vean todo o nada
        return nombre_seccion in self.permisos_secciones

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

def vacaciones_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    nombre_empleado = slugify(str(instance.empleado.nombre))
    
    # 1. OBTENER FECHAS DESDE EL JSON
    # d_sel es una lista de strings ej: ["2026-04-25", "2026-04-20"]
    d_sel = instance.dias_seleccionados
    
    if d_sel and isinstance(d_sel, list):
        # Ordenamos para asegurar que el nombre del archivo sea consistente (Inicio a Fin)
        fechas_ordenadas = sorted(d_sel)
        f_inicio_str = fechas_ordenadas[0]
        f_fin_str = fechas_ordenadas[-1]
    else:
        # Respaldo en caso de que la lista llegue vacía por algún error
        hoy = date.today().strftime('%Y-%m-%d')
        f_inicio_str = hoy
        f_fin_str = hoy

    # 2. DETERMINAR EL AÑO PARA LA CARPETA
    # Extraemos el año del primer string de la lista (YYYY-MM-DD)
    anio_vacacion = f_inicio_str.split('-')[0]
    
    # 3. LÓGICA DE DISTINCIÓN DE CAMPO
    tipo_doc = "formato"
    if hasattr(instance, '_current_file_field'):
        tipo_doc = instance._current_file_field
    
    # El nombre quedará ej: formato_2026-04-20_a_2026-04-25.pdf
    nuevo_nombre = f"{tipo_doc}_{f_inicio_str}_a_{f_fin_str}.{ext}"
    
    return os.path.join('expedientes', nombre_empleado, 'vacaciones', anio_vacacion, nuevo_nombre)

class Vacacion(models.Model):
    class EstadoVacacion(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de Aprobación'
        APROBADO = 'APROBADO', 'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    # Relación principal
    empleado = models.ForeignKey(
        'Empleado', 
        on_delete=models.CASCADE, 
        related_name='vacaciones',
        verbose_name="Empleado"
    )

    dias_seleccionados = models.JSONField(null=True, blank=True, verbose_name="Días específicos")
    
    # Puede ser una relación a otro Empleado o un CharField si solo guardas el nombre
    autorizador = models.ForeignKey(
        'Empleado',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vacaciones_autorizadas',
        verbose_name="Jefe de Departamento que autorizó"
    )

    autorizador_firmado = models.BooleanField(
        default=False, 
        verbose_name="Jefe firmó"
    )
    
    autorizador_fecha_firma = models.DateTimeField(
        null=True, 
        blank=True
    )

    gerente_autorizador = models.ForeignKey(
        'Empleado',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vacaciones_autorizadas_gerencia',
        verbose_name="Gerente que autorizó"
    )

    gerente_firmado = models.BooleanField(
        default=False, 
        verbose_name="Gerente firmó"
    )
    
    gerente_fecha_firma = models.DateTimeField(
        null=True, 
        blank=True
    )

    # Documentación
    archivo_vacaciones = models.FileField(
        upload_to=vacaciones_directory_path,
        null=True,
        blank=True,
        verbose_name="Formato de Vacaciones (PDF)"
    )
    
    archivo_roles = models.FileField(
        upload_to=vacaciones_directory_path,
        null=True,
        blank=True,
        verbose_name="Formato de Roles y Pendientes"
    )

    requiere_respuesta_automatica = models.BooleanField(
        default=False, 
        verbose_name="¿Requiere respuesta automática?"
    )

    requiere_redireccion = models.BooleanField(default=False)
    
    empleados_redireccion = models.ManyToManyField(
        'Empleado',
        blank=True,
        related_name='redirecciones_asignadas',
        verbose_name="Empleados asignados para redirección"
    )

    # Control de estado y auditoría
    estado = models.CharField(
        max_length=20,
        choices=EstadoVacacion.choices,
        default=EstadoVacacion.PENDIENTE
    )
    
    observaciones = models.TextField(
        blank=True, 
        help_text="Notas adicionales sobre la ausencia."
    )
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Como ya no hay fecha_inicio, usamos el conteo o el primer elemento
        total = self.total_dias
        return f"Vacaciones {self.empleado.nombre} ({total} días)"

    @property
    def total_dias(self):
        # Ahora solo contamos el largo de la lista JSON
        return len(self.dias_seleccionados) if self.dias_seleccionados else 0
    
    @property
    def periodos_agrupados(self):
        """
        Detecta días consecutivos y los agrupa en intervalos.
        Retorna: [{'inicio': date, 'fin': date, 'es_rango': bool, 'cantidad': int}]
        """
        if not self.dias_seleccionados:
            return []

        # 1. Convertir strings a objetos date y ordenar
        from datetime import datetime, timedelta
        fechas = sorted([datetime.strptime(d, '%Y-%m-%d').date() for d in self.dias_seleccionados])
        
        if not fechas:
            return []

        periodos = []
        inicio_actual = fechas[0]
        anterior = fechas[0]
        conteo_bloque = 1 # Inicializamos el contador del bloque

        for i in range(1, len(fechas)):
            actual = fechas[i]
            if actual == anterior + timedelta(days=1):
                conteo_bloque += 1 # Es consecutivo, sumamos al bloque
            else:
                # No es consecutivo, cerramos el periodo actual
                periodos.append({
                    'inicio': inicio_actual,
                    'fin': anterior,
                    'es_rango': inicio_actual != anterior,
                    'cantidad': conteo_bloque # <--- AGREGAMOS ESTO
                })
                # Reiniciamos para el nuevo bloque
                inicio_actual = actual
                conteo_bloque = 1
            anterior = actual

        # Añadir el último bloque procesado
        periodos.append({
            'inicio': inicio_actual,
            'fin': anterior,
            'es_rango': inicio_actual != anterior,
            'cantidad': conteo_bloque
        })

        return periodos
    
    class Meta:
        verbose_name = "Vacación"
        verbose_name_plural = "Vacaciones"
        # Cambiamos el ordenamiento ya que fecha_inicio no existe
        ordering = ['-fecha_solicitud']

def incapacidad_directory_path(instance, filename):
    # 1. Obtener la extensión original (pdf, jpg, etc.)
    ext = filename.split('.')[-1]
    
    # 2. Limpiar el nombre del empleado para la carpeta raíz
    nombre_empleado = slugify(str(instance.empleado.nombre))
    
    # 3. Formatear la fecha de inicio para el nombre del archivo (Ej: 2026-03-15)
    f_inicio = instance.fecha_inicio.strftime('%Y-%m-%d')
    
    # 4. Crear un nombre de archivo que indique de qué trata el documento
    # Ejemplo: incapacidad_2026-03-15_3-dias.pdf
    nuevo_nombre = f"incapacidad_{f_inicio}_{instance.duracion_dias}-dias.{ext}"
    
    # 5. Organizar por el año de la incapacidad
    anio_incapacidad = instance.fecha_inicio.year
    
    # Resultado: media/expedientes/juan-perez/incapacidades/2026/incapacidad_2026-03-15_3-dias.pdf
    return os.path.join('expedientes', nombre_empleado, 'incapacidades', str(anio_incapacidad), nuevo_nombre)

class Incapacidad(models.Model):
    # Relación con el empleado
    empleado = models.ForeignKey(
        'Empleado', 
        on_delete=models.CASCADE, 
        related_name='incapacidades',
        verbose_name="Empleado"
    )

    # Datos básicos de la ausencia
    fecha_inicio = models.DateField(
        verbose_name="Fecha de Inicio",
        help_text="Primer día de la incapacidad según el documento"
    )
    
    duracion_dias = models.PositiveIntegerField(
        verbose_name="Días de duración",
        help_text="Cantidad de días autorizados"
    )

    # El documento escaneado/foto (Lo más importante)
    archivo = models.FileField(
        upload_to=incapacidad_directory_path,
        verbose_name="Documento del IMSS",
        help_text="Copia digital de la incapacidad"
    )

    # Notas y Control
    observaciones = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Observaciones"
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Incapacidad"
        verbose_name_plural = "Incapacidades"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Incapacidad {self.empleado.nombre} - {self.fecha_inicio}"

    @property
    def fecha_fin(self):
        # Cálculo automático del último día de incapacidad
        return self.fecha_inicio + timezone.timedelta(days=self.duracion_dias - 1)
    
class Tarea(models.Model):
    class EstadoTarea(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        EN_PROGRESO = 'EN_PROGRESO', 'En Progreso'
        COMPLETADA = 'COMPLETADA', 'Completada' # Tarea hecha por el empleado
        FINALIZADA = 'FINALIZADA', 'Finalizada' # Tarea revisada/cerrada por Admin

    class Prioridad(models.TextChoices):
        BAJA = 'BAJA', 'Baja'
        MEDIA = 'MEDIA', 'Media'
        ALTA = 'ALTA', 'Alta'

    empleado = models.ForeignKey(
        'Empleado', # Usamos string por si está definido abajo
        on_delete=models.CASCADE,
        related_name='tareas', # Clave para acceder desde el empleado (empleado.tareas.all)
        verbose_name="Asignado a"
    )
    
    fecha_completado = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Fecha en que se completó"
    )

    titulo = models.CharField(max_length=200, verbose_name="Título de la tarea")
    descripcion = models.TextField(blank=True, verbose_name="Descripción detallada")
    
    estado = models.CharField(
        max_length=20,
        choices=EstadoTarea.choices,
        default=EstadoTarea.PENDIENTE,
        verbose_name="Estado"
    )

    enlace = models.URLField(max_length=500, blank=True, null=True, verbose_name="Enlace de la tarea")
    
    prioridad = models.CharField(
        max_length=10,
        choices=Prioridad.choices,
        default=Prioridad.MEDIA,
        verbose_name="Prioridad"
    )

    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name="Fecha Límite")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    objeto_id = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="ID del objeto relacionado"
    )
    tipo_objeto = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        help_text="Ej: vacacion, incapacidad, expediente"
    )
    
    def __str__(self):
        return f"{self.titulo} - {self.empleado.nombre}"

    class Meta:
        verbose_name = "Tarea / Asunto"
        verbose_name_plural = "Tareas / Asuntos"
        ordering = ['estado', 'fecha_vencimiento'] # Muestra primero las pendientes