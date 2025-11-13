from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.EmployeesView, name='employees'),
    path('empleado/edit/<int:empleado_id>/', views.EditEmpleadoView, name='edit_empleado'),
    path('search-employee/', views.SearchEmployeesView, name='search_employees'),
]