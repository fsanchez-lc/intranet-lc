from django.urls import path
from . import views

app_name = 'service_stations'

urlpatterns = [
    path('', views.ServiceStationView, name='service_station_url')
]