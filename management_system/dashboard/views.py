from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def DashboardView(request):
    context = {
        'title': 'Panel de Control',
    }
    return render(request, 'home.html', context)
