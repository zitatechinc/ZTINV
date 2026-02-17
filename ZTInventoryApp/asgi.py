"""
ASGI config for ZTInventoryApp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ZTInventoryApp.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import ims.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            ims.routing.websocket_urlpatterns
        )
    ),
})
