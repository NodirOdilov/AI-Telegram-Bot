"""Модели диалогов и сообщений."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel, SoftDeletableModel, TimeStampedModel


class Conversation(BaseModel, SoftDeletableModel):
    """Диалог пользователя с AI-ассистентом."""

    class Source(models.TextChoices):
        TELEGRAM = "telegram", _("Telegram")
        WEB = "web", _("Web")
        API = "api", _("API")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    title = models.CharField(max_length=256, blank=True, default="")
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.WEB)
    model = models.CharField(max_length=64, default="gpt-4o-mini")
    system_prompt = models.TextField(blank=True, default="")

    # Идентификатор внешней системы (например, chat_id Telegram)
    external_chat_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("диалог")
        verbose_name_plural = _("диалоги")
        ordering = ("-last_message_at", "-created_at")
        indexes = [
            models.Index(fields=["user", "source"]),
            models.Index(fields=["external_chat_id"]),
        ]

    def __str__(self) -> str:
        return self.title or f"Диалог {self.pk}"


class Message(BaseModel):
    """Отдельное сообщение в диалоге."""

    class Role(models.TextChoices):
        SYSTEM = "system", _("Системное")
        USER = "user", _("Пользователь")
        ASSISTANT = "assistant", _("Ассистент")
        TOOL = "tool", _("Инструмент")
        FUNCTION = "function", _("Функция")

    class Status(models.TextChoices):
        PENDING = "pending", _("В обработке")
        STREAMING = "streaming", _("Стриминг")
        COMPLETED = "completed", _("Готово")
        FAILED = "failed", _("Ошибка")
        CANCELLED = "cancelled", _("Отменено")

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages",
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.COMPLETED)

    # Метаданные инструментов
    tool_name = models.CharField(max_length=128, blank=True, default="")
    tool_arguments = models.JSONField(default=dict, blank=True)
    tool_response = models.JSONField(default=dict, blank=True)

    # Стоимость
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)

    # Идентификатор внешней системы (telegram message id)
    external_message_id = models.CharField(max_length=64, blank=True, default="")
    reply_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies",
    )

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("сообщение")
        verbose_name_plural = _("сообщения")
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["role", "status"]),
        ]


class Attachment(BaseModel):
    """Вложение к сообщению (изображение, аудио, документ)."""

    class Kind(models.TextChoices):
        IMAGE = "image", _("Изображение")
        AUDIO = "audio", _("Аудио")
        VIDEO = "video", _("Видео")
        DOCUMENT = "document", _("Документ")
        VOICE = "voice", _("Голосовое")
        STICKER = "sticker", _("Стикер")

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="attachments",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    file = models.FileField(upload_to="attachments/%Y/%m/")
    file_size = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=128, blank=True, default="")
    duration_seconds = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)

    external_file_id = models.CharField(max_length=256, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("вложение")
        verbose_name_plural = _("вложения")


class ConversationContext(TimeStampedModel):
    """Сжатый контекст диалога для экономии токенов."""

    conversation = models.OneToOneField(
        Conversation, on_delete=models.CASCADE, related_name="context",
    )
    summary = models.TextField(blank=True, default="")
    embedded_vector = models.JSONField(default=list, blank=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("контекст диалога")
        verbose_name_plural = _("контексты диалогов")
