from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.ResourcesView, name='resources'),
    path('api/search-documentos/', views.BuscarDocumentosView, name='search_documentos'),
    path('cursos/edit/<int:curso_id>/', views.CursoEditView, name='edit_curso'),
    path('documento/<int:documento_id>/edit/', views.edit_documento, name='edit_documento'),
    path('documento/<int:documento_id>/archive/', views.archive_documento, name='archive_documento'),
]