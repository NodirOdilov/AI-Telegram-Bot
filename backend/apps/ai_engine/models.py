"""Модели каталога моделей ИИ и шаблонов промптов."""
from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel, TimeStampedModel


class AIProvider(BaseModel):
    """Поставщик AI: OpenAI, Anthropic, Google, локальный и т.д."""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    base_url = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("поставщик ИИ")
        verbose_name_plural = _("поставщики ИИ")

    def __str__(self) -> str:
        return self.name


class AIModel(BaseModel):
    """Конкретная модель ИИ с прайсингом и параметрами."""

    class Modality(models.TextChoices):
        CHAT = "chat", _("Чат")
        IMAGE = "image", _("Изображение")
        AUDIO = "audio", _("Аудио")
        VISION = "vision", _("Vision")
        EMBEDDING = "embedding", _("Эмбеддинги")
        TTS = "tts", _("Синтез речи")

    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, related_name="models")
    code = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    modality = models.CharField(max_length=16, choices=Modality.choices)

    context_window = models.PositiveIntegerField(default=0)
    max_output_tokens = models.PositiveIntegerField(default=0)

    input_token_price = models.DecimalField(
        max_digits=12, decimal_places=8, default=Decimal("0"),
    )
    output_token_price = models.DecimalField(
        max_digits=12, decimal_places=8, default=Decimal("0"),
    )
    image_price = models.DecimalField(
        max_digits=12, decimal_places=6, default=Decimal("0"),
    )
    audio_minute_price = models.DecimalField(
        max_digits=12, decimal_places=6, default=Decimal("0"),
    )

    supports_functions = models.BooleanField(default=False)
    supports_vision = models.BooleanField(default=False)
    supports_streaming = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    parameters = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("модель ИИ")
        verbose_name_plural = _("модели ИИ")
        ordering = ("provider", "code")

    def __str__(self) -> str:
        return f"{self.provider.code}/{self.code}"


class PromptTemplate(BaseModel):
    """Шаблон промпта (системного или пользовательского)."""

    class Kind(models.TextChoices):
        SYSTEM = "system", _("Системный")
        USER = "user", _("Пользовательский")
        TOOL = "tool", _("Инструмент")

    code = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True, default="")
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.SYSTEM)
    language = models.CharField(max_length=8, default="ru")
    content = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("шаблон промпта")
        verbose_name_plural = _("шаблоны промптов")


class AIRequestLog(TimeStampedModel):
    """Журнал запросов в провайдеры ИИ для отладки и аудита."""

    provider = models.CharField(max_length=64)
    model = models.CharField(max_length=128)
    endpoint = models.CharField(max_length=128)
    request_payload = models.JSONField(default=dict)
    response_payload = models.JSONField(default=dict)
    status_code = models.PositiveSmallIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    duration_ms = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("запрос к ИИ")
        verbose_name_plural = _("запросы к ИИ")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["provider", "model", "created_at"]),
        ]
