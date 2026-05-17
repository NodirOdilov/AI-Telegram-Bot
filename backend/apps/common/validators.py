"""Кастомные валидаторы для моделей и сериализаторов."""
from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

TELEGRAM_USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,31}$")


def validate_telegram_username(value: str) -> None:
    """Проверяет корректность Telegram-имени пользователя."""
    if not TELEGRAM_USERNAME_RE.match(value):
        raise ValidationError(_("Некорректное имя пользователя Telegram."))


def validate_positive(value) -> None:
    if value is None or value < 0:
        raise ValidationError(_("Значение должно быть положительным."))


def validate_language_code(value: str) -> None:
    if not re.match(r"^[a-z]{2}(-[A-Z]{2})?$", value or ""):
        raise ValidationError(_("Некорректный код языка."))
