"""Менеджеры моделей пользователей.

Поддерживается создание обычных пользователей, суперпользователей
и пользователей, пришедших из Telegram (без email и пароля).
"""
from __future__ import annotations

from typing import Any

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import BaseUserManager
from django.db import transaction


class UserManager(BaseUserManager):
    """Менеджер для кастомной модели User."""

    use_in_migrations = True

    def _create_user(
        self,
        email: str | None,
        password: str | None,
        **extra_fields: Any,
    ):
        """Внутренний метод создания пользователя."""
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password) if password else make_password(None)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self,
        email: str,
        password: str,
        **extra_fields: Any,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields["is_staff"] is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields["is_superuser"] is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")
        return self._create_user(email, password, **extra_fields)

    @transaction.atomic
    def get_or_create_telegram_user(
        self,
        telegram_id: int,
        *,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str | None = None,
    ) -> tuple["AbstractUser", bool]:  # noqa: F821
        """Идемпотентно создаёт или обновляет пользователя по Telegram ID."""
        from .models import TelegramProfile, User

        profile = (
            TelegramProfile.objects.select_related("user")
            .filter(telegram_id=telegram_id)
            .first()
        )
        if profile:
            user = profile.user
            updated_fields: list[str] = []
            if username and profile.username != username:
                profile.username = username
                updated_fields.append("username")
            if first_name and profile.first_name != first_name:
                profile.first_name = first_name
                updated_fields.append("first_name")
            if last_name and profile.last_name != last_name:
                profile.last_name = last_name
                updated_fields.append("last_name")
            if language_code and profile.language_code != language_code:
                profile.language_code = language_code
                updated_fields.append("language_code")
            if updated_fields:
                profile.save(update_fields=updated_fields)
            return user, False

        display_name = " ".join(filter(None, [first_name, last_name])) or username or f"tg{telegram_id}"
        user = self.create_user(
            email=None,
            password=None,
            display_name=display_name,
            language=(language_code or "ru")[:2],
        )
        TelegramProfile.objects.create(
            user=user,
            telegram_id=telegram_id,
            username=username or "",
            first_name=first_name or "",
            last_name=last_name or "",
            language_code=language_code or "ru",
        )
        return user, True
