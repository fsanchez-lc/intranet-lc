from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from equipment import views as equipment_views
from django.conf.urls.static import static
<<<<<<< HEAD
from django.conf import settings  # <--- AÑADE ESTA LÍNEA
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
=======
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
>>>>>>> ba46064 (Settings modificados por statics)

urlpatterns = [
    path('admin/', admin.site.urls),

    path("__reload__/", include("django_browser_reload.urls")),

    # URL principal o por defecto
    path('', include('dashboard.urls')),

    # URLS de las apps
    path('usuarios/', include('users.urls', namespace='users_urls')),
    path('repositorio/', include('resources.urls', namespace='resources_urls')),
    path('guias/', include('guides.urls', namespace='guides_urls')),

    path('equipos/', equipment_views.EquipmentView, name='lista_equipos'),
    path('equipos/crear/', equipment_views.CreateEquipmentView, name='crear_equipo_url'),
    path('empleados/', include('employees.urls')),
    path('tipos-equipos/', equipment_views.TypeEquipmentView, name='type_equipment_url'),
    path('equipos/editar/<int:pk>/', equipment_views.EditEquipmentView, name='editar_equipo_url'),
    path('equipos/eliminar/<int:pk>/', equipment_views.DeactivateEquipmentView, name='eliminar_equipo_url'),
    path('estaciones-servicio/', include('service_stations.urls', namespace='service_station_urls')),
    path('tickets/', include('tickets.urls', namespace='tickets_urls')),
    path('reportes/', include('reports.urls', namespace='reports_urls')),
    path('administrador/', include('administrator.urls')),
    path('dinamicas/', include('dinamicas.urls')),
    
    # path('asistente-ia/', include('asistente-ia.urls', namespace='asistente-ia')),
    # path('permisos/', include('permisos.urls', namespace='permisos')),
    # ---- FIN DEL BLOQUE COMENTADO ----

    # Login y logout usando las vistas de Django
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()