from django.db import models
from django.conf import settings

class ServiceStation(models.Model):
    """
    Representa una estación de servicio, sucursal o ubicación física de la empresa.
    """
    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('CERRADA', 'Cerrada'),
    ]

    nombre = models.CharField(
        max_length=200, 
        unique=True, 
        help_text="Nombre único de la estación de servicio."
    )
    descripcion = models.TextField(
        blank=True, 
        help_text="Descripción detallada o notas adicionales sobre la estación."
    )
    ubicacion = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Dirección física o descripción de la ubicación (ej: 'Edificio B, Piso 3')."
    )
    telefono = models.CharField(max_length=20, blank=True, help_text="Teléfono de contacto de la estación.")
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='ACTIVA')
    
    responsable = models.ForeignKey(
        'employees.Empleado',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estaciones_a_cargo",
        help_text="Empleado responsable o gerente de la estación."
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Estación de Servicio"
        verbose_name_plural = "Estaciones de Servicio"
        ordering = ['nombre']

