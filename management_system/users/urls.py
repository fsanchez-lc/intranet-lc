from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.UsersView, name='users'),
    path('search-user/', views.SearchUsuarioView, name='search_users'),
    path('usuario/edit/<int:pk>/', views.EditUsuarioView, name='edit_usuario'),
]