# Server/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from accounts.consumers import PaymentConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Server.settings')

django_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/payments/", PaymentConsumer.as_asgi()),
        ])
    ),
})
