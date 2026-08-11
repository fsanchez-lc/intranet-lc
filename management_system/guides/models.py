from django.db import models

# Create your models here.
class Guia(models.Model):
    SISTEMA_CHOICES = [
        ('SLAM', 'SLAM'),
        ('SICA', 'SICA'),
    ]
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    sistema = models.CharField(
        max_length=4, 
        choices=SISTEMA_CHOICES, 
        default='SLAM'
    )
    orden = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['orden'] # <--- Esto ordena los acordeones automáticamente

    def __str__(self):
        return f"[{self.sistema}] {self.orden} - {self.titulo}"    

class Paso(models.Model):
    guia = models.ForeignKey(Guia, related_name='pasos', on_delete=models.CASCADE)
    orden = models.PositiveIntegerField() # Para controlar el 1, 2, 3...
    instruccion = models.TextField()
    imagen = models.ImageField(upload_to='guias/pasos/')

    class Meta:
        ordering = ['orden']