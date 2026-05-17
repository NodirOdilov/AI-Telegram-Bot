"""Реестр и базовый класс плагинов."""
from __future__ import annotations

import importlib
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from django.core.cache import cache

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PluginResult:
    """Результат выполнения плагина."""

    success: bool
    data: dict
    error: str | None = None


class BasePlugin(ABC):
    """Абстрактный базовый класс плагина."""

    code: str
    name: str
    description: str = ""
    schema: dict = {}

    @abstractmethod
    def execute(self, arguments: dict, *, user=None, config: dict | None = None) -> PluginResult:
        """Выполняет действие плагина."""


class PluginRegistry:
    """Менеджер плагинов: загрузка, кэширование, поиск."""

    CACHE_KEY = "plugins:registry"
    CACHE_TTL = 600

    @classmethod
    def list_active(cls):
        from .models import Plugin

        cached = cache.get(cls.CACHE_KEY)
        if cached is not None:
            return cached
        plugins = list(Plugin.objects.filter(is_active=True))
        cache.set(cls.CACHE_KEY, plugins, cls.CACHE_TTL)
        return plugins

    @classmethod
    def invalidate(cls) -> None:
        cache.delete(cls.CACHE_KEY)

    @classmethod
    def load_handler(cls, plugin) -> BasePlugin | None:
        if not plugin.handler_path:
            return None
        try:
            module_path, attr = plugin.handler_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            handler_class = getattr(module, attr)
            return handler_class()
        except Exception:
            logger.exception("Не удалось загрузить обработчик плагина %s", plugin.code)
            return None

    @classmethod
    def invoke(cls, plugin, arguments: dict, *, user=None, conversation=None) -> PluginResult:
        from .models import PluginConfig, PluginInvocation

        handler = cls.load_handler(plugin)
        if handler is None:
            return PluginResult(success=False, data={}, error="Обработчик плагина не найден.")

        config_obj = (
            PluginConfig.objects.filter(plugin=plugin, user=user).first()
            if user else None
        )
        start = time.perf_counter()
        try:
            result = handler.execute(
                arguments,
                user=user,
                config=(config_obj.config if config_obj else {}),
            )
            status = (
                PluginInvocation.Status.SUCCESS if result.success
                else PluginInvocation.Status.FAILED
            )
            PluginInvocation.objects.create(
                user=user,
                plugin=plugin,
                conversation=conversation,
                status=status,
                arguments=arguments,
                result=result.data,
                error_message=result.error or "",
                duration_ms=int((time.perf_counter() - start) * 1000),
            )
            return result
        except Exception as exc:
            logger.exception("Ошибка выполнения плагина %s", plugin.code)
            PluginInvocation.objects.create(
                user=user,
                plugin=plugin,
                conversation=conversation,
                status=PluginInvocation.Status.FAILED,
                arguments=arguments,
                result={},
                error_message=str(exc),
                duration_ms=int((time.perf_counter() - start) * 1000),
            )
            return PluginResult(success=False, data={}, error=str(exc))

    @classmethod
    def get_function_schemas(cls, user=None) -> list[dict]:
        """Возвращает список JSON-схем плагинов для function calling."""
        from .models import PluginConfig

        plugins = cls.list_active()
        if user is not None:
            disabled = set(
                PluginConfig.objects.filter(user=user, is_enabled=False)
                .values_list("plugin_id", flat=True)
            )
            plugins = [p for p in plugins if p.id not in disabled]

        return [
            {
                "type": "function",
                "function": {
                    "name": plugin.code,
                    "description": plugin.description,
                    "parameters": plugin.schema or {"type": "object", "properties": {}},
                },
            }
            for plugin in plugins
        ]
