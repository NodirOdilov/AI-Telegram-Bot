"""Модели Telegram-интеграции."""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel, TimeStampedModel


class TelegramUpdate(TimeStampedModel):
    """Журнал входящих обновлений Telegram."""

    class Status(models.TextChoices):
        RECEIVED = "received", _("Получено")
        PROCESSING = "processing", _("В обработке")
        PROCESSED = "processed", _("Обработано")
        FAILED = "failed", _("Ошибка")

    update_id = models.BigIntegerField(unique=True, db_index=True)
    payload = models.JSONField()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.RECEIVED,
    )
    error_message = models.TextField(blank=True, default="")
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("обновление Telegram")
        verbose_name_plural = _("обновления Telegram")
        ordering = ("-created_at",)


class TelegramCommand(BaseModel):
    """Описание команды бота для меню."""

    code = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=256)
    handler = models.CharField(max_length=128)
    requires_admin = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = _("команда Telegram")
        verbose_name_plural = _("команды Telegram")
        ordering = ("sort_order", "code")
