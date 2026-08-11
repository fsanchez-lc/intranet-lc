from django.shortcuts import render
from navigation.utils import with_menu
from django.contrib.auth.decorators import login_required
from .decorators import validar_acceso_menu  # Asegúrate de importar tu decorador

@login_required
@validar_acceso_menu  # <--- Agregamos esto para proteger la entrada directa
def MenuView(request):
    # with_menu(request) ahora devuelve solo los ítems que el usuario puede ver
    return render(request, 'navigation/base.html', with_menu(request))