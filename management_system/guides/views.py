from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Guia, Paso


# Create your views here.
@login_required
def GuidesView(request):

    empleado = request.user.empleado 
    guias = Guia.objects.prefetch_related('pasos').all()
    
    context = {
        'guias': guias,
        'empleado': empleado,
    }
    return render(request, 'guide.html', context)