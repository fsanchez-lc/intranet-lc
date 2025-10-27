from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def ServiceStationView(request):
    return render(request, 'service_stations.html', {})
