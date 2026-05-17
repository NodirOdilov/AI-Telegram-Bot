"""Дополнительные классы аутентификации для DRF.

* ``TelegramAuthentication`` — извлекает Telegram-пользователя из заголовка
  ``X-Telegram-Init-Data`` (для мини-приложений) или ``X-Telegram-User-Id``.
* ``APIKeyAuthentication`` — авторизация по выпущенному API-ключу.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import parse_qsl

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

from .models import APIKey, TelegramProfile

logger = logging.getLogger(__name__)
User = get_user_model()


class TelegramAuthentication(authentication.BaseAuthentication):
    """Проверяет подпись initData мини-приложения Telegram."""

    INIT_DATA_HEADER = "HTTP_X_TELEGRAM_INIT_DATA"
    USER_ID_HEADER = "HTTP_X_TELEGRAM_USER_ID"

    def authenticate(self, request) -> tuple[Any, Any] | None:
        init_data = request.META.get(self.INIT_DATA_HEADER)
        user_id_header = request.META.get(self.USER_ID_HEADER)

        if init_data:
            user_id = self._verify_init_data(init_data)
        elif user_id_header:
            user_id = int(user_id_header)
        else:
            return None

        try:
            profile = TelegramProfile.objects.select_related("user").get(
                telegram_id=user_id,
            )
        except TelegramProfile.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed(
                "Telegram-пользователь не найден.",
            ) from exc

        if not profile.user.is_active:
            raise exceptions.AuthenticationFailed("Аккаунт деактивирован.")

        return profile.user, None

    def _verify_init_data(self, init_data: str) -> int:
        """Валидирует HMAC подпись initData."""
        bot_token = settings.TELEGRAM_BOT_TOKEN
        if not bot_token:
            raise exceptions.AuthenticationFailed("Telegram токен не настроен.")

        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            raise exceptions.AuthenticationFailed("Подпись отсутствует.")

        # Срок жизни initData
        auth_date = int(parsed.get("auth_date", 0))
        if auth_date and (time.time() - auth_date > 86400):
            raise exceptions.AuthenticationFailed("Подпись просрочена.")

        data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated, received_hash):
            raise exceptions.AuthenticationFailed("Подпись initData не совпадает.")

        # Извлекаем user.id из поля user (JSON)
        import json

        user_json = parsed.get("user", "{}")
        user_payload = json.loads(user_json)
        return int(user_payload["id"])


class APIKeyAuthentication(authentication.BaseAuthentication):
    """Проверяет наличие действующего API-ключа в заголовке Authorization."""

    KEYWORD = "Token"

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.KEYWORD.lower().encode():
            return None
        if len(auth) != 2:
            raise exceptions.AuthenticationFailed("Некорректный формат токена.")

        raw_key = auth[1].decode()
        prefix = raw_key[:12]
        digest = hashlib.sha256(raw_key.encode()).hexdigest()

        try:
            api_key = APIKey.objects.select_related("user").get(
                key_prefix=prefix, key_hash=digest,
            )
        except APIKey.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Недействительный токен.") from exc

        if not api_key.is_valid():
            raise exceptions.AuthenticationFailed("Токен отозван или просрочен.")

        # Обновляем метку последнего использования
        APIKey.objects.filter(pk=api_key.pk).update(last_used_at=time.time())
        return api_key.user, api_key
