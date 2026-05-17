"""Модели плагинов."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel, TimeStampedModel


class Plugin(BaseModel):
    """Описание плагина (инструмента) для AI."""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    version = models.CharField(max_length=32, default="1.0.0")
    homepage = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(
        default=True,
        help_text=_("Доступен ли плагин всем пользователям по умолчанию"),
    )

    # Описание схемы параметров для function calling
    schema = models.JSONField(default=dict, blank=True)
    config_schema = models.JSONField(default=dict, blank=True)

    # Класс-обработчик в виде пути импорта
    handler_path = models.CharField(max_length=256, blank=True, default="")

    class Meta:
        verbose_name = _("плагин")
        verbose_name_plural = _("плагины")
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} v{self.version}"


class PluginConfig(TimeStampedModel):
    """Настройки плагина для конкретного пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="plugin_configs",
    )
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name="configs")
    is_enabled = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("user", "plugin")
        verbose_name = _("настройка плагина")
        verbose_name_plural = _("настройки плагинов")


class PluginInvocation(TimeStampedModel):
    """Журнал вызовов плагинов."""

    class Status(models.TextChoices):
        SUCCESS = "success", _("Успех")
        FAILED = "failed", _("Ошибка")
        TIMEOUT = "timeout", _("Тайм-аут")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="plugin_invocations",
        null=True, blank=True,
    )
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name="invocations")
    conversation = models.ForeignKey(
        "conversations.Conversation",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="plugin_invocations",
    )
    status = models.CharField(max_length=16, choices=Status.choices)
    arguments = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")
    duration_ms = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("вызов плагина")
        verbose_name_plural = _("вызовы плагинов")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["plugin", "status", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]
