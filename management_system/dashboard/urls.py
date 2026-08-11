from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView, name='home'),
    path('dashboard-1/', views.DashboardsVariosView, {'template_name': 'dashboard-1.html'}, name='dashboard_1'),
    path('dashboard-2/', views.DashboardsVariosView, {'template_name': 'dashboard-2.html'}, name='dashboard_2'),
    path('dashboard-3/', views.DashboardsVariosView, {'template_name': 'dashboard-3.html'}, name='dashboard_3'),

    path('cambiar-estado/<int:tarea_id>/', views.CambiarEstadoTareaView, name='cambiar_estado_tarea'),
    path('validar-acceso-reporte/', views.ValidarAccesoReporteView, name='validar_acceso_reporte'),
]