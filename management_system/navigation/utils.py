# navigation/utils.py

from .models import MenuItem

def get_menu_items_for_user(user):
    if user.is_authenticated:
        return MenuItem.objects.filter(
            parent=None,
            groups__in=user.groups.all()
        ).distinct().order_by('order')
    return MenuItem.objects.none()


def with_menu(request, context=None):
    if context is None:
        context = {}
    menu_items = get_menu_items_for_user(request.user)
    context['menu_items'] = menu_items
    return context