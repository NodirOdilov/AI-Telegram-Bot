"""Модели приложения пользователей.

Содержит:
* ``User`` — кастомная модель пользователя на основе email.
* ``TelegramProfile`` — связь с Telegram-аккаунтом.
* ``Role`` и ``UserRole`` — расширенная ролевая модель доступа.
* ``UserPreference`` — пользовательские настройки.
* ``AuditLog`` — журнал действий.
* ``APIKey`` — программный доступ к API.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel, TimeStampedModel

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Кастомная модель пользователя на основе UUID и email."""

    class AccountType(models.TextChoices):
        TELEGRAM = "telegram", _("Telegram-пользователь")
        EMAIL = "email", _("Email-пользователь")
        SERVICE = "service", _("Сервисный аккаунт")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email"), unique=True, null=True, blank=True)
    display_name = models.CharField(_("отображаемое имя"), max_length=128)
    avatar = models.ImageField(_("аватар"), upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(_("описание"), blank=True, default="")

    account_type = models.CharField(
        _("тип аккаунта"),
        max_length=16,
        choices=AccountType.choices,
        default=AccountType.EMAIL,
    )

    language = models.CharField(_("язык"), max_length=8, default="ru")
    timezone = models.CharField(_("часовой пояс"), max_length=64, default="Asia/Tashkent")

    is_active = models.BooleanField(_("активен"), default=True)
    is_staff = models.BooleanField(_("сотрудник"), default=False)
    is_verified = models.BooleanField(_("подтверждён"), default=False)

    # Двухфакторная аутентификация
    two_factor_enabled = models.BooleanField(_("включён 2FA"), default=False)
    two_factor_secret = models.CharField(max_length=64, blank=True, default="")

    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = _("пользователь")
        verbose_name_plural = _("пользователи")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["account_type", "is_active"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return self.display_name or (self.email or str(self.id))

    @property
    def telegram_id(self) -> int | None:
        profile = getattr(self, "telegram_profile", None)
        return profile.telegram_id if profile else None

    def deactivate(self) -> None:
        self.is_active = False
        self.save(update_fields=["is_active"])


class TelegramProfile(TimeStampedModel):
    """Telegram-профиль, привязанный к пользователю."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_profile",
    )
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=64, blank=True, default="")
    first_name = models.CharField(max_length=128, blank=True, default="")
    last_name = models.CharField(max_length=128, blank=True, default="")
    language_code = models.CharField(max_length=8, blank=True, default="ru")

    is_premium = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    chat_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    last_seen_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _("Telegram-профиль")
        verbose_name_plural = _("Telegram-профили")
        indexes = [
            models.Index(fields=["telegram_id"]),
            models.Index(fields=["chat_id"]),
        ]

    def __str__(self) -> str:
        return f"@{self.username}" if self.username else f"tg:{self.telegram_id}"

    def touch(self) -> None:
        self.last_seen_at = timezone.now()
        self.save(update_fields=["last_seen_at"])


class Role(BaseModel):
    """Роль доступа, сгруппированная в RBAC."""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    permissions = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = _("роль")
        verbose_name_plural = _("роли")

    def __str__(self) -> str:
        return self.name


class UserRole(TimeStampedModel):
    """Связка пользователя и роли с указанием срока действия."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="granted_roles",
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "role")
        verbose_name = _("назначение роли")
        verbose_name_plural = _("назначения ролей")

    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at < timezone.now())


class UserPreference(TimeStampedModel):
    """Пользовательские настройки бота."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    preferred_model = models.CharField(max_length=64, default="gpt-4o-mini")
    max_tokens = models.PositiveIntegerField(default=1200)
    temperature = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("1.00"),
    )
    image_model = models.CharField(max_length=64, default="dall-e-3")
    image_quality = models.CharField(max_length=16, default="hd")
    tts_voice = models.CharField(max_length=32, default="alloy")
    stream_responses = models.BooleanField(default=True)
    show_usage = models.BooleanField(default=False)
    voice_only = models.BooleanField(default=False)

    enabled_features = models.JSONField(default=dict, blank=True)
    custom_prompt = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = _("настройка пользователя")
        verbose_name_plural = _("настройки пользователей")


class AuditLog(TimeStampedModel):
    """Журнал ключевых действий пользователей и системы."""

    class Action(models.TextChoices):
        LOGIN = "login", _("Вход")
        LOGOUT = "logout", _("Выход")
        CREATE = "create", _("Создание")
        UPDATE = "update", _("Обновление")
        DELETE = "delete", _("Удаление")
        PERMISSION = "permission", _("Изменение прав")
        PAYMENT = "payment", _("Платёж")
        SYSTEM = "system", _("Системное событие")

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_actions",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    target_type = models.CharField(max_length=64, blank=True, default="")
    target_id = models.CharField(max_length=64, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = _("запись аудита")
        verbose_name_plural = _("журнал аудита")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
        ]


class APIKey(BaseModel):
    """API-ключ для программного доступа к публичному REST API."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    name = models.CharField(max_length=128)
    key_prefix = models.CharField(max_length=12, db_index=True)
    key_hash = models.CharField(max_length=128)
    scopes = models.JSONField(default=list, blank=True)

    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("API ключ")
        verbose_name_plural = _("API ключи")

    def is_valid(self) -> bool:
        if self.revoked:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
