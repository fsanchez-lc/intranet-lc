from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.EmployeesView, name='employees'),
    path('crear/', views.CrearEmpleadoView, name='crear_empleado'),
]