"""Модели уведомлений."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel, TimeStampedModel


class NotificationTemplate(BaseModel):
    """Шаблон уведомления для разных каналов."""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    subject = models.CharField(max_length=256, blank=True, default="")
    body_text = models.TextField()
    body_html = models.TextField(blank=True, default="")
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("шаблон уведомления")
        verbose_name_plural = _("шаблоны уведомлений")


class Notification(BaseModel):
    """Конкретное уведомление, сохранённое в БД."""

    class Status(models.TextChoices):
        PENDING = "pending", _("В очереди")
        SENT = "sent", _("Отправлено")
        FAILED = "failed", _("Ошибка")
        READ = "read", _("Прочитано")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=256)
    body = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    channels = models.JSONField(default=list, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = _("уведомление")
        verbose_name_plural = _("уведомления")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "status"]),
        ]


class Broadcast(BaseModel):
    """Массовая рассылка."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Черновик")
        SCHEDULED = "scheduled", _("Запланирована")
        RUNNING = "running", _("Выполняется")
        COMPLETED = "completed", _("Завершена")
        FAILED = "failed", _("Ошибка")

    title = models.CharField(max_length=256)
    body = models.TextField()
    channels = models.JSONField(default=list, blank=True)
    audience_filter = models.JSONField(default=dict, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("рассылка")
        verbose_name_plural = _("рассылки")
        ordering = ("-created_at",)
