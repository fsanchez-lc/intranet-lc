from django.db import models
from django.contrib.auth.models import Group, User

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"

class Permiso(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Nombre corto de la política o permiso (ej: Política de correo electrónico)")
    descripcion = models.TextField(blank=True, help_text="Descripción detallada de lo que permite este permiso.")

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"

class Empleado(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, # O models.CASCADE si prefieres
        related_name="empleado",   # Así puedes hacer request.user.empleado
        null=True, 
        blank=True,
        verbose_name="Usuario del Sistema"
    )

    class EstadoEmpleado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'

    nombre = models.CharField(max_length=255, help_text="Nombre completo del empleado.")
    email = models.EmailField(unique=True, help_text="Correo electrónico del empleado.")
    telefono = models.CharField(max_length=20, blank=True)
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    posicion = models.CharField(max_length=100, blank=True, help_text="Ej: Coordinadora de RRHH")

    estacion_servicio = models.ForeignKey(
        'service_stations.ServiceStation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empleados",
        help_text="Estación de servicio a la que está asignado el empleado."
    )

    grupos = models.ManyToManyField(
        Group,
        blank=True,
        related_name="empleados",
        verbose_name="Tipos de Usuario",
        help_text="Tipo de usuario al que pertenece el empleado. El administrador define sus permisos."
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoEmpleado.choices,
        default=EstadoEmpleado.ACTIVO
    )
        
    politicas_permisos = models.ManyToManyField(
        Permiso,
        blank=True,
        related_name="empleados_con_permiso",
        verbose_name="Políticas y Permisos Individuales",
        help_text="Permisos específicos asignados directamente a este empleado."
    )

    firma_digital = models.ImageField(
        upload_to='firmas_empleados/',
        null=True,
        blank=True,
        help_text="Sube una imagen de la firma digital del empleado."
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
