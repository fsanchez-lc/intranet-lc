from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.TicketsView, name='tickets_url'),
    path('crear/', views.CreateTicketView, name="create_ticket"),
]