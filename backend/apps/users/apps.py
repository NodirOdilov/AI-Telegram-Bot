"""Конфигурация приложения users."""
from __future__ import annotations

from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    verbose_name = "Пользователи"

    def ready(self) -> None:
        # Импорт сигналов выполняется здесь, чтобы они зарегистрировались
        # один раз во время загрузки приложения.
        from . import signals  # noqa: F401
