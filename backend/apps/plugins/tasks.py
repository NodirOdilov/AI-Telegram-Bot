"""Celery задачи плагинов."""
from __future__ import annotations

from celery import shared_task

from .registry import PluginRegistry


@shared_task(name="apps.plugins.tasks.refresh_plugin_cache")
def refresh_plugin_cache() -> int:
    """Обновляет кэш реестра плагинов."""
    PluginRegistry.invalidate()
    return len(PluginRegistry.list_active())
