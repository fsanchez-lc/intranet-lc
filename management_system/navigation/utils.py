from .models import MenuItem

def with_menu(request, context=None):
    if context is None:
        context = {}
    
    user = request.user
    if not user.is_authenticated:
        return context

    # 1. Traemos todos los padres
    all_parents = MenuItem.objects.filter(parent=None).order_by('order').prefetch_related('children', 'groups')
    
    filtered_menu = []

    for item in all_parents:
        # 2. ¿El usuario puede ver el padre?
        if can_see_item(user, item):
            # 3. Filtrar hijos del padre
            allowed_children = []
            for child in item.children.all().order_by('order'):
                if can_see_item(user, child):
                    allowed_children.append(child)
            
            # 4. Adjuntar hijos permitidos y ver si alguno está activo
            item.allowed_children = allowed_children
            item.is_active_child = any(child.url == request.path for child in allowed_children)
            
            filtered_menu.append(item)

    context['menu_items'] = filtered_menu
    return context

def can_see_item(user, item):
    """Lógica de visibilidad estricta"""
    if user.is_superuser:
        return True
    
    # Si el menú no tiene grupos, es público (se muestra a todos los logueados)
    if not item.groups.exists():
        return True
    
    # Si tiene grupos, el usuario debe pertenecer a al menos uno
    user_group_ids = user.groups.values_list('id', flat=True)
    return item.groups.filter(id__in=user_group_ids).exists()