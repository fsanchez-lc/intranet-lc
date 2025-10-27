from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _

class Usuario(AbstractUser):
    # Mantenemos el email como único y obligatorio, pero no para el login.
    email = models.EmailField('correo electrónico', unique=True)

    # --- CONFIGURACIÓN DE AUTENTICACIÓN ---
    # Le decimos a Django que el campo para iniciar sesión será el 'username' (comportamiento por defecto).
    USERNAME_FIELD = 'username'
    
    # Campos requeridos al crear un superusuario (además de username y password).
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="usuario_set",
        related_query_name="usuario",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="usuario_permissions_set",
        related_query_name="usuario",
    )

    def __str__(self):
        # Es más útil mostrar el username o el nombre en las listas que el email, si este no es el login.
        return self.username

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

