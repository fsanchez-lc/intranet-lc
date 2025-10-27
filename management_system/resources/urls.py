from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.ResourcesView, name='resources'),
    path('api/search-documentos/', views.BuscarDocumentosView, name='search_documentos'),
    path('cursos/edit/<int:curso_id>/', views.CursoEditView, name='edit_curso'),
]