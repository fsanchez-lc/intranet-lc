from django.db import models
from django.utils import timezone


class Ticket(models.Model):
    class Prioridad(models.TextChoices):
        BAJA = 'BAJA', 'Baja'
        MEDIA = 'MEDIA', 'Media'
        ALTA = 'ALTA', 'Alta'

    class Estado(models.TextChoices):
        ABIERTO = 'ABIERTO', 'Abierto'
        ASIGNADO = 'ASIGNADO', 'Asignado'
        EN_PROCESO = 'EN_PROCESO', 'En Proceso'
        CERRADO = 'CERRADO', 'Cerrado'

    folio = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True, 
        null=True, 
        verbose_name="Folio",
        help_text="Folio único generado automáticamente (Ej. TKT-00001)."
    )
    
    titulo = models.CharField(max_length=200, help_text="Título breve y descriptivo del ticket.")
    descripcion = models.TextField(help_text="Descripción detallada del problema o solicitud.")
    
    prioridad = models.CharField(
        max_length=10,
        choices=Prioridad.choices,
        default=Prioridad.MEDIA
    )
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.ABIERTO
    )

    observaciones = models.TextField(
        blank=True, 
        help_text="Notas de seguimiento, comentarios o resolución del ticket."
    )

    departamento_destino = models.ForeignKey(
        'employees.Departamento',
        on_delete=models.PROTECT,
        related_name="tickets_recibidos",
        verbose_name="Departamento Destino",
        help_text="Área corporativa responsable de solucionar este ticket."
    )
    
    asignado_a = models.ForeignKey(
        'employees.Empleado',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets_asignados",
        verbose_name="Asignado a",
        help_text="Empleado específico del departamento que resolverá el problema."
    )

    # --- Relaciones con otros modelos ---
    creado_por = models.ForeignKey(
        'employees.Empleado',
        on_delete=models.PROTECT,
        related_name="tickets_creados",
        help_text="Empleado que creó el ticket."
    )
    estacion_servicio = models.ForeignKey(
        'service_stations.ServiceStation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
        help_text="Estación de servicio relacionada con el ticket."
    )

    # --- Campos de fecha ---
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    fecha_cerrado = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Fecha de Cierre",
        help_text="Se actualiza automáticamente cuando el ticket se marca como 'Cerrado'."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Guarda el estado original para detectar cambios al guardar
        self.__original_estado = self.estado

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para gestionar la fecha de cierre
        basándose en el estado del ticket.
        """
        # Si el estado cambia a 'CERRADO'
        if self.estado == self.Estado.CERRADO and self.__original_estado != self.Estado.CERRADO:
            self.fecha_cerrado = timezone.now()
        # Si se reabre un ticket que estaba cerrado
        elif self.estado != self.Estado.CERRADO and self.__original_estado == self.Estado.CERRADO:
            self.fecha_cerrado = None
        
        super().save(*args, **kwargs)
        # Actualiza el estado original para la próxima vez
        self.__original_estado = self.estado

    def __str__(self):
        return f"Ticket #{self.id}: {self.titulo}"

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-fecha_creacion']

class Comentario(models.Model):
    class Tipo(models.TextChoices):
        COMENTARIO = 'COMENTARIO', 'Comentario'
        ASIGNACION = 'ASIGNACION', 'Asignación'
        CAMBIO_ESTADO = 'CAMBIO_ESTADO', 'Cambio de estado'
        RESOLUCION = 'RESOLUCION', 'Resolución'
    
    class Visibilidad(models.TextChoices):
        PUBLICO = 'PUBLICO', 'Público'
        PRIVADO = 'PRIVADO', 'Privado'

    ticket = models.ForeignKey(
        Ticket, 
        on_delete=models.CASCADE, 
        related_name="comentarios",
        help_text="Ticket al que pertenece este comentario."
    )
    autor = models.ForeignKey(
        'employees.Empleado',
        on_delete=models.PROTECT,
        related_name="comentarios",
        help_text="Empleado que escribió el comentario."
    )
    texto = models.TextField(verbose_name="Comentario")
    
    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.COMENTARIO
    )
    visibilidad = models.CharField(
        max_length=10,
        choices=Visibilidad.choices,
        default=Visibilidad.PUBLICO
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)