from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

# Usamos un decorador para registrar el modelo Usuario con una configuración personalizada.
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # Define qué columnas se muestran en la lista de usuarios.
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')

    fieldsets = UserAdmin.fieldsets

    # Añade filtros en la barra lateral del admin.
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

