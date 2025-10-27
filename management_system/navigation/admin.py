from django.contrib import admin
from .models import MenuItem

# Register your models here.
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')  # columnas que se mostrarán en la lista
    filter_horizontal = ('groups',)  # para seleccionar grupos más fácilmente