"""Конфигурация приложения common."""
from __future__ import annotations

from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Регистрирует общие утилиты, middleware и базовые классы."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
    verbose_name = "Общие компоненты"
