"""Корневой URL-конфигуратор проекта.

Здесь регистрируются: административная панель, REST API,
WebSocket (через ASGI), документация OpenAPI, метрики Prometheus,
health-check эндпоинты и webhook для Telegram.
"""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Административная панель
    path("admin/", admin.site.urls),

    # REST API (версионированное)
    path("api/v1/", include(("apps.api.urls", "api"), namespace="api-v1")),

    # OpenAPI документация
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Webhook Telegram
    path("telegram/", include(("apps.telegram_bot.urls", "telegram"), namespace="telegram")),

    # Метрики Prometheus
    path("", include("django_prometheus.urls")),

    # Healthcheck
    path("health/", include("health_check.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path("silk/", include("silk.urls", namespace="silk")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
