from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.ResourcesView, name='resources'),
    path('search/documentos/', views.BuscarDocumentosView, name='search_documentos'),
    path('search/formatos/', views.BuscarFormatosView, name='search_formatos'),
    path('search/videos/', views.BuscarVideosView, name='search_videos'),
    path('curso/edit/<int:curso_id>/', views.CursoEditView, name='edit_curso'),
    path('documento/edit/<int:documento_id>/', views.edit_documento, name='edit_documento'),
    path('video/edit/<int:video_id>/', views.VideoEditView, name='edit_video'),
    path('slide/edit/<int:slide_id>/', views.SlideEditView, name='edit_slide'),
    path('curso/inscribir/<int:curso_id>/', views.InscribirCursoView, name='inscribir_curso'),
]