from django.db import models
from django.conf import settings

class TipoEquipo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    # Útil para agrupar: ej. ¿Es de TI, es de Seguridad, es Uniforme?
    categoria_general = models.CharField(max_length=50, blank=True, null=True, 
                                         help_text="Ej. Tecnología, Seguridad, Vehículos, Ropa")

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Tipo de Equipo"
        verbose_name_plural = "Tipos de Equipo"

class EstadoEquipo(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Condición física: Ej. Nuevo, Bueno, Regular, Dañado")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Estado Físico"
        verbose_name_plural = "Estados Físicos"


class Equipo(models.Model):
    class EstatusDisponibilidad(models.TextChoices):
        BODEGA = 'BODEGA', 'En Bodega'
        ASIGNADO = 'ASIGNADO', 'Asignado'
        MANTENIMIENTO = 'MANTENIMIENTO', 'En Mantenimiento'
        BAJA = 'BAJA', 'Baja / Desechado'
        PERDIDO = 'PERDIDO', 'Robado / Extraviado'

    class EstadoRegistro(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'

    # Datos Generales
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo del equipo")
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # Clasificación y Condición
    tipo_equipo = models.ForeignKey(TipoEquipo, on_delete=models.PROTECT, null=True, blank=True)
    estado_fisico = models.ForeignKey(EstadoEquipo, on_delete=models.PROTECT, null=True, blank=True)
    estatus = models.CharField(max_length=20, choices=EstatusDisponibilidad.choices, default=EstatusDisponibilidad.BODEGA)
    
    # Administrativo y Financiero
    costo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Costo de adquisición")
    proveedor = models.CharField(max_length=150, blank=True)
    fecha_compra = models.DateField(null=True, blank=True)
    vencimiento_garantia = models.DateField(null=True, blank=True)
    
    # Evidencia
    foto = models.ImageField(upload_to='equipos/fotos/', null=True, blank=True, help_text="Foto del equipo o herramienta")
    observaciones = models.TextField(blank=True, help_text="Detalles sobre raspones, fallas o particularidades.")

    # Ubicación actual (si no está asignado a un empleado, puede estar fijo en una estación)
    estacion_servicio = models.ForeignKey(
        'service_stations.ServiceStation',
        on_delete=models.SET_NULL, null=True, blank=True, related_name="equipos_fijos"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    estado_registro = models.CharField(max_length=10, choices=EstadoRegistro.choices, default=EstadoRegistro.ACTIVO)

    def save(self, *args, **kwargs):
        if not self.numero_serie:
            self.numero_serie = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.numero_serie or 'S/N'})"

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ['-fecha_creacion']


# NUEVO MODELO: Para rastrear quién tiene qué a lo largo del tiempo
class AsignacionEquipo(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="asignaciones")
    empleado = models.ForeignKey('employees.Empleado', on_delete=models.CASCADE, related_name="equipos_asignados")
    
    fecha_asignacion = models.DateField(auto_now_add=True)
    fecha_devolucion = models.DateField(null=True, blank=True, help_text="Se llena cuando el empleado devuelve el equipo")
    
    # Puedes enlazar esto a tu sistema de expedientes para guardar el PDF firmado
    archivo_responsiva = models.FileField(upload_to='equipos/responsivas/', null=True, blank=True)
    
    notas_entrega = models.TextField(blank=True, help_text="Ej. Se entrega con cargador y funda.")
    notas_devolucion = models.TextField(blank=True, help_text="Ej. Pantalla estrellada al devolver.")

    @property
    def esta_activo(self):
        return self.fecha_devolucion is None

    def __str__(self):
        return f"{self.equipo.nombre} asignado a {self.empleado.nombre}"

    class Meta:
        verbose_name = "Asignación de Equipo"
        verbose_name_plural = "Historial de Asignaciones"
        ordering = ['-fecha_asignacion']