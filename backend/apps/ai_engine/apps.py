"""Конфигурация приложения ai_engine."""
from __future__ import annotations

from django.apps import AppConfig


class AiEngineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_engine"
    verbose_name = "AI движок"
