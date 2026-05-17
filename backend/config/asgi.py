"""ASGI точка входа для развёртывания с поддержкой WebSocket.

Реализует ProtocolTypeRouter, который маршрутизирует HTTP-запросы
в стандартное Django ASGI-приложение, а WebSocket-соединения — через
аутентификацию и маршруты канала из ``apps.api.routing``.
"""
from __future__ import annotations

import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

# Импорт после django.setup, иначе модели ещё не зарегистрированы
from apps.api.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
