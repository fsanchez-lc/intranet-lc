from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Empleado

@receiver(post_save, sender=Empleado)
def create_user_for_new_employee(sender, instance, created, **kwargs):
    """
    Esta señal se dispara cada vez que un Empleado es guardado.
    Si el Empleado es NUEVO ('created' es True), crea un User de Django.
    """
    if created:
        # 1. Comprueba si ya existe un usuario con ese email
        if User.objects.filter(email=instance.email).exists():
            # Si ya existe (ej. un admin), solo lo enlazamos
            user = User.objects.get(email=instance.email)
            instance.user = user
            instance.save()
        else:
            # 2. Si no existe, crea un nuevo User
            # Usamos la contraseña por defecto que tenías en tu 'save'
            default_password = 'sistemas1864' 
            
            user = User.objects.create_user(
                username=instance.email,  # Usamos email como username
                email=instance.email,
                password=default_password,
                first_name=instance.nombre  # Opcional, pero útil
            )
            
            # 3. Enlaza el User recién creado con el Empleado
            instance.user = user
            instance.save()
        
        if user is not None:
            try:
                # Busca el grupo. Si no existe, lo crea.
                empleado_group, group_created = Group.objects.get_or_create(name="Empleado")
                # Añade el usuario a ese grupo
                user.groups.add(empleado_group)
            except Exception as e:
                print(f"Error al asignar grupo al usuario {user.username}: {e}")