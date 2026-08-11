from functools import wraps
from django.core.exceptions import PermissionDenied
from .models import MenuItem

def validar_acceso_menu(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        
        # 1. Superusuario siempre pasa
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # 2. Identificar la ruta
        current_path = request.path
        
        # 3. Buscar el ítem del menú por URL
        # IMPORTANTE: Asegúrate que en la BD las URLs terminen en / si así están en tus urls.py
        menu_item = MenuItem.objects.filter(url=current_path).first()

        # 4. Si la URL no está registrada en el sistema de menús, 
        # asumimos que no tiene restricciones por esta vía.
        if not menu_item:
            return view_func(request, *args, **kwargs)

        # 5. Lógica de Grupos (Espejo de utils.py)
        if menu_item.groups.exists():
            user_group_ids = request.user.groups.values_list('id', flat=True)
            has_permission = menu_item.groups.filter(id__in=user_group_ids).exists()
            
            if not has_permission:
                print(f"BLOQUEO: Usuario {request.user} intentó entrar a {current_path} sin permiso.")
                raise PermissionDenied
        
        # Si no tiene grupos o el usuario tiene el grupo, pasa.
        return view_func(request, *args, **kwargs)

    return _wrapped_view