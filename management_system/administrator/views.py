from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import JsonResponse
from .models import SeccionSistema

@login_required
def AdministratorView(request):

    return render(request, 'admin.html', {})

def ConfiguracionView(request):
    grupos = Group.objects.all()
    secciones = SeccionSistema.objects.prefetch_related('permisos').all()

    data = []
    for seccion in secciones:
        permisos = list(seccion.permisos.values('id', 'name', 'codename'))
        data.append({
            'id': seccion.id,
            'nombre': seccion.nombre,
            'descripcion': seccion.descripcion,
            'permisos': permisos
        })
    return JsonResponse({'secciones': data})
