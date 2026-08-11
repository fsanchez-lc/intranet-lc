from django.db import models
from django.contrib.auth.models import User

class LogConsultaReporte(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=255) # Ejemplo: "Acceso concedido", "Clave incorrecta"
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.fecha_hora}"