from django.db import models
from django.conf import settings

class TipoEquipo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Tipo de Equipo"
        verbose_name_plural = "Tipos de Equipo"

class EstadoEquipo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Estado de Equipo"
        verbose_name_plural = "Estados de Equipo"

class Equipo(models.Model):

    class EstadoRegistro(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'

    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo del equipo, ej: Impresora HP LaserJet Pro")
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, unique=True, help_text="Número de serie único del equipo", blank=True,  
    null=True)
    
    tipo_equipo = models.ForeignKey(
        TipoEquipo,
        on_delete=models.PROTECT, # Evita borrar un tipo si hay equipos que lo usan
        null=True, 
        blank=True
    )
    estado = models.ForeignKey(
        EstadoEquipo,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    
    asignado_a = models.ForeignKey(
        'employees.Empleado',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipos_asignados",
        help_text="Empleado al que está asignado el equipo."
    )

    estacion_servicio = models.ForeignKey(
        'service_stations.ServiceStation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipos",
        help_text="Estación de servicio a la que pertenece el equipo."
    )
    
    fecha_compra = models.DateField(null=True, blank=True)
    vencimiento_garantia = models.DateField(null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    estado_registro = models.CharField(
        max_length=10,
        choices=EstadoRegistro.choices,
        default=EstadoRegistro.ACTIVO
    )

    def save(self, *args, **kwargs):
        if not self.numero_serie:
            self.numero_serie = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.numero_serie or 'N/A'})"

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ['-fecha_creacion']

