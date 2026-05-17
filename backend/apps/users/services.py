"""Сервисный слой для приложения users."""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import APIKey, AuditLog

User = get_user_model()


@dataclass(slots=True)
class IssuedKey:
    """Результат выпуска API-ключа: модель и сырое значение."""

    api_key: APIKey
    raw_key: str


class APIKeyService:
    """Сервис управления API-ключами."""

    PREFIX_LENGTH = 12

    @classmethod
    @transaction.atomic
    def issue(
        cls,
        user,
        name: str,
        scopes: list[str] | None = None,
        expires_at=None,
    ) -> IssuedKey:
        """Выпускает новый API-ключ. Возвращает модель и сырое значение."""
        raw_key = secrets.token_urlsafe(32)
        prefix = raw_key[: cls.PREFIX_LENGTH]
        digest = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = APIKey.objects.create(
            user=user,
            name=name,
            key_prefix=prefix,
            key_hash=digest,
            scopes=scopes or [],
            expires_at=expires_at,
        )
        AuditLog.objects.create(
            actor=user,
            action=AuditLog.Action.CREATE,
            target_type="APIKey",
            target_id=str(api_key.id),
            payload={"name": name, "scopes": scopes or []},
        )
        return IssuedKey(api_key=api_key, raw_key=raw_key)

    @classmethod
    @transaction.atomic
    def revoke(cls, api_key: APIKey, actor=None) -> None:
        api_key.revoked = True
        api_key.save(update_fields=["revoked"])
        AuditLog.objects.create(
            actor=actor,
            action=AuditLog.Action.UPDATE,
            target_type="APIKey",
            target_id=str(api_key.id),
            payload={"revoked": True},
        )


class AuditService:
    """Удобный фасад для записи событий аудита."""

    @staticmethod
    def log(actor, action: str, target=None, payload: dict | None = None, request=None) -> None:
        ip = None
        user_agent = ""
        if request is not None:
            ip = request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT", "")
        AuditLog.objects.create(
            actor=actor,
            action=action,
            target_type=target.__class__.__name__ if target else "",
            target_id=str(getattr(target, "pk", "")) if target else "",
            payload=payload or {},
            ip_address=ip,
            user_agent=user_agent,
        )
