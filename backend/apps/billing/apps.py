"""Конфигурация приложения billing."""
from __future__ import annotations

from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"
    verbose_name = "Биллинг"

    def ready(self) -> None:
        from . import signals  # noqa: F401
