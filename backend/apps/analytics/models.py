"""Модели аналитики и журналов потребления."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel, TimeStampedModel


class UsageEvent(BaseModel):
    """Событие потребления ресурса (унифицированная таблица)."""

    class Kind(models.TextChoices):
        CHAT = "chat", _("Чат")
        IMAGE = "image", _("Изображение")
        VISION = "vision", _("Vision")
        TRANSCRIPTION = "transcription", _("Распознавание речи")
        TTS = "tts", _("Синтез речи")
        TOOL = "tool", _("Инструмент")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usage_events",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices, db_index=True)
    model = models.CharField(max_length=128, blank=True, default="")

    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    units = models.PositiveIntegerField(default=0, help_text=_("Изображения, секунды, символы и т.п."))
    cost = models.DecimalField(max_digits=14, decimal_places=6, default=Decimal("0"))

    conversation = models.ForeignKey(
        "conversations.Conversation",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="usage_events",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("событие потребления")
        verbose_name_plural = _("события потребления")
        indexes = [
            models.Index(fields=["user", "kind", "created_at"]),
            models.Index(fields=["kind", "created_at"]),
        ]
        ordering = ("-created_at",)


class DailyUsage(TimeStampedModel):
    """Суммарное потребление за день (агрегат)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_usage",
    )
    date = models.DateField(db_index=True)
    tokens = models.PositiveBigIntegerField(default=0)
    images = models.PositiveIntegerField(default=0)
    transcription_seconds = models.PositiveIntegerField(default=0)
    tts_characters = models.PositiveIntegerField(default=0)
    vision_requests = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=14, decimal_places=6, default=Decimal("0"))

    class Meta:
        unique_together = ("user", "date")
        ordering = ("-date",)
        verbose_name = _("ежедневное потребление")
        verbose_name_plural = _("ежедневное потребление")


class SystemMetric(TimeStampedModel):
    """Системная метрика (произвольное численное значение)."""

    key = models.CharField(max_length=128, db_index=True)
    value = models.DecimalField(max_digits=20, decimal_places=6)
    labels = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = _("системная метрика")
        verbose_name_plural = _("системные метрики")
        indexes = [
            models.Index(fields=["key", "timestamp"]),
        ]
