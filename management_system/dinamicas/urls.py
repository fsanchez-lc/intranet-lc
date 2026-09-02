from django.urls import path
from . import views

urlpatterns = [
    path('regata/', views.vista_regata, name='juego_regata'),
]