from django.db import models

# Create your models here.
from django.contrib.auth.models import Group

class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200, blank=True, null=True) #URL o Nombre de ruta
    icon = models.CharField(max_length=50, blank=True, null=True) #Iconos FontAwesome
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    order = models.PositiveIntegerField(default=0)
    groups = models.ManyToManyField(Group, blank=True, related_name='menu_items') #A que rol es visible

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name