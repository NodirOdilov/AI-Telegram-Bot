"""Встроенные плагины: погода, поиск, dictionary и т.д.

Каждый плагин реализует интерфейс ``BasePlugin`` и регистрируется
в БД при выполнении management-команды ``register_plugins``.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import requests

from .registry import BasePlugin, PluginResult

logger = logging.getLogger(__name__)


class WeatherPlugin(BasePlugin):
    """Получение текущей погоды через open-meteo (без API-ключа)."""

    code = "weather"
    name = "Погода"
    description = "Возвращает текущую погоду по координатам или названию города."
    schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Название города"},
            "latitude": {"type": "number"},
            "longitude": {"type": "number"},
        },
    }

    def execute(self, arguments: dict, *, user=None, config: dict | None = None) -> PluginResult:
        latitude = arguments.get("latitude")
        longitude = arguments.get("longitude")
        city = arguments.get("city")

        if city and (latitude is None or longitude is None):
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "ru"},
                timeout=10,
            ).json()
            if not geo.get("results"):
                return PluginResult(False, {}, f"Город «{city}» не найден.")
            latitude = geo["results"][0]["latitude"]
            longitude = geo["results"][0]["longitude"]

        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,wind_speed_10m,relative_humidity_2m",
                "timezone": "auto",
            },
            timeout=10,
        ).json()
        return PluginResult(True, response)


class CurrentTimePlugin(BasePlugin):
    """Возвращает текущее время сервера."""

    code = "current_time"
    name = "Текущее время"
    description = "Возвращает текущее серверное время."
    schema = {"type": "object", "properties": {}}

    def execute(self, arguments: dict, *, user=None, config: dict | None = None) -> PluginResult:
        return PluginResult(True, {"iso": datetime.utcnow().isoformat() + "Z"})


class WebSearchPlugin(BasePlugin):
    """Поиск в DuckDuckGo."""

    code = "web_search"
    name = "Поиск в интернете"
    description = "Выполняет поиск в DuckDuckGo и возвращает топ результатов."
    schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Поисковый запрос"},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["query"],
    }

    def execute(self, arguments: dict, *, user=None, config: dict | None = None) -> PluginResult:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return PluginResult(False, {}, "Модуль duckduckgo_search не установлен.")
        query = arguments["query"]
        limit = int(arguments.get("limit", 5))
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=limit))
            return PluginResult(True, {"results": results})
        except Exception as exc:
            return PluginResult(False, {}, str(exc))


BUILTIN_PLUGINS: list[tuple[type[BasePlugin], str]] = [
    (WeatherPlugin, "apps.plugins.builtins.WeatherPlugin"),
    (CurrentTimePlugin, "apps.plugins.builtins.CurrentTimePlugin"),
    (WebSearchPlugin, "apps.plugins.builtins.WebSearchPlugin"),
]
