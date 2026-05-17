"""Общие утилиты, не привязанные к конкретному домену."""
from __future__ import annotations

import hashlib
import json
import secrets
from decimal import Decimal
from typing import Any


def generate_token(length: int = 32) -> str:
    """Генерирует криптостойкий токен."""
    return secrets.token_urlsafe(length)


def stable_hash(payload: Any) -> str:
    """Стабильное SHA-256 от JSON-сериализуемого объекта."""
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def safe_decimal(value: Any, default: Decimal | None = None) -> Decimal:
    """Безопасное приведение к Decimal."""
    try:
        return Decimal(str(value))
    except Exception:
        return default if default is not None else Decimal("0")


def chunked(iterable, size: int):
    """Разбивает итерируемое на чанки заданного размера."""
    buffer: list = []
    for item in iterable:
        buffer.append(item)
        if len(buffer) >= size:
            yield buffer
            buffer = []
    if buffer:
        yield buffer


def truncate(text: str, limit: int = 4096, suffix: str = "...") -> str:
    """Урезает строку до ``limit`` символов."""
    if len(text) <= limit:
        return text
    return text[: max(0, limit - len(suffix))] + suffix


def mask_secret(value: str, visible: int = 4) -> str:
    """Маскирует секрет, оставляя видимыми последние ``visible`` символов."""
    if not value:
        return ""
    if len(value) <= visible:
        return "*" * len(value)
    return "*" * (len(value) - visible) + value[-visible:]
