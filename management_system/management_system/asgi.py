import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import dinamicas.routing  # Crearemos este archivo en el paso 6

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'management_system.settings')

application = ProtocolTypeRouter({
    # El tráfico web normal HTTP sigue funcionando igual
    "http": get_asgi_application(),
    
    # El tráfico WebSocket se redirige a nuestra app de dinámicas
    "websocket": AuthMiddlewareStack(
        URLRouter(
            dinamicas.routing.websocket_urlpatterns
        )
    ),
})