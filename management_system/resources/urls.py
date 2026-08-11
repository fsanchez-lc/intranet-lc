from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.ResourcesView, name='resources'),
    path('search/documentos/', views.BuscarDocumentosView, name='search_documentos'),
    path('search/formatos/', views.BuscarFormatosView, name='search_formatos'),
    path('search/videos/', views.BuscarVideosView, name='search_videos'),
    path('search/certificados/', views.BuscarCertificadosView, name='search_certificados'),
    path('search/historial/', views.BuscarHistorialView, name='search_historial'),

    path('curso/edit/<int:curso_id>/', views.CursoEditView, name='edit_curso'),
    path('documento/edit/<int:documento_id>/', views.edit_documento, name='edit_documento'),
    path('video/edit/<int:video_id>/', views.VideoEditView, name='edit_video'),
    path('slide/edit/<int:slide_id>/', views.SlideEditView, name='edit_slide'),
    path('curso/inscribir/<int:curso_id>/', views.InscribirCursoView, name='inscribir_curso'),

    path('api/get-historial-empleado/', views.GetHistorialEmpleadoView, name='get_historial_empleado'),
    path('api/update-certificacion/<int:inscripcion_id>/', views.UpdateCertificacionView, name='update_certificacion'),

    path('get-procesos/', views.GetProcesosView, name='get_procesos'),
    path('get-procedimientos/', views.GetProcedimientosView, name='get_procedimientos'),
]