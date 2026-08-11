from django.db import models
from django.contrib.auth.models import Permission

class SeccionSistema(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    permisos = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.nombre