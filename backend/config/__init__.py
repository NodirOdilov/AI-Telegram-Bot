"""Конфигурационный пакет проекта.

Здесь экспортируется приложение Celery, чтобы при запуске Django
оно регистрировалось автоматически и было доступно через ``shared_task``.
"""
from __future__ import annotations

from .celery import app as celery_app

__all__ = ("celery_app",)
