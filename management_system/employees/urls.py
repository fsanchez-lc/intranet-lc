from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.EmployeesView, name='employees'),
    path('recrear-expedientes-manual/', views.admin_recrear_expedientes, name='ejecutar_recreacion'),

    path('empleado/edit/<int:empleado_id>/', views.EditEmpleadoView, name='edit_empleado'),
    path('search-employee/', views.SearchEmployeesView, name='search_employees'),
    path('search-vacations/', views.SearchVacationsView, name='search_vacations'),
    path('crear-expediente/', views.AddExpedienteView, name='crear_expediente'),
    path('expediente/carga-masiva/', views.CargaMasivaExpedienteView, name='carga_masiva_expediente'),
    path('expediente/mapear-archivos/', views.MapearArchivosView, name='mapear_archivos'),
    path('expediente/editar/<int:expediente_id>/', views.EditExpedienteView, name='editar_expediente'),
    path('expediente/bajar/<int:expediente_id>/', views.BajarExpedienteView, name='bajar_expediente'),
    path('expediente/eliminar/<int:expediente_id>/', views.EliminarExpedienteView, name='eliminar_expediente_db'),
    path('empleado/foto/<int:empleado_id>/', views.UpdateFotoEmpleadoView, name='actualizar_foto'),
    path('empleados/carga-masiva-fotos/', views.CargaMasivaFotosView, name='carga_masiva_fotos'),   
    path('vacaciones/solicitar/', views.AddVacacionSolicitudView, name='crear_vacacion'),
    path('vacaciones/editar/<int:vacacion_id>/', views.EditVacacionView, name='editar_vacacion'),
    path('vacaciones/<int:vacacion_id>/firmar/', views.FirmarVacacionView, name='firmar_vacacion'),
    path('incapacidades/solicitar/', views.AddIncapacidadView, name='crear_incapacidad'),
    path('incapacidades/editar/<int:incapacidad_id>/', views.EditIncapacidadView, name='editar_incapacidad'),
    path('search-incapacidades/', views.SearchIncapacidadesView, name='search_incapacidades'),
    path('api/mi-departamento/jefes/', views.get_jefes_departamento, name='get_jefes_departamento'),

]