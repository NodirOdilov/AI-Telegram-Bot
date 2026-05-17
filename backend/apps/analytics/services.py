"""Сервисный слой аналитики."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from .models import DailyUsage, UsageEvent


class UsageRecorder:
    """Регистрирует события потребления и обновляет ежедневные агрегаты."""

    @classmethod
    @transaction.atomic
    def record_chat(
        cls,
        user,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: Decimal,
        conversation=None,
    ) -> UsageEvent:
        total = prompt_tokens + completion_tokens
        event = UsageEvent.objects.create(
            user=user,
            kind=UsageEvent.Kind.CHAT,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            cost=cost,
            conversation=conversation,
        )
        cls._bump_daily(user, tokens=total, cost=cost)
        return event

    @classmethod
    @transaction.atomic
    def record_image(cls, user, model: str, prompt: str, cost: Decimal) -> UsageEvent:
        event = UsageEvent.objects.create(
            user=user,
            kind=UsageEvent.Kind.IMAGE,
            model=model,
            units=1,
            cost=cost,
            metadata={"prompt": prompt[:1000]},
        )
        cls._bump_daily(user, images=1, cost=cost)
        return event

    @classmethod
    @transaction.atomic
    def record_transcription(cls, user, duration: float) -> UsageEvent:
        event = UsageEvent.objects.create(
            user=user,
            kind=UsageEvent.Kind.TRANSCRIPTION,
            units=int(duration),
        )
        cls._bump_daily(user, transcription_seconds=int(duration))
        return event

    @classmethod
    @transaction.atomic
    def record_tts(cls, user, characters: int) -> UsageEvent:
        event = UsageEvent.objects.create(
            user=user,
            kind=UsageEvent.Kind.TTS,
            units=characters,
        )
        cls._bump_daily(user, tts_characters=characters)
        return event

    @classmethod
    @transaction.atomic
    def record_vision(cls, user, prompt_tokens: int = 0, cost: Decimal = Decimal("0")):
        event = UsageEvent.objects.create(
            user=user,
            kind=UsageEvent.Kind.VISION,
            prompt_tokens=prompt_tokens,
            total_tokens=prompt_tokens,
            cost=cost,
        )
        cls._bump_daily(user, vision_requests=1, cost=cost, tokens=prompt_tokens)
        return event

    @staticmethod
    def _bump_daily(
        user,
        *,
        tokens: int = 0,
        images: int = 0,
        transcription_seconds: int = 0,
        tts_characters: int = 0,
        vision_requests: int = 0,
        cost: Decimal = Decimal("0"),
    ) -> None:
        today = timezone.now().date()
        DailyUsage.objects.get_or_create(user=user, date=today)
        DailyUsage.objects.filter(user=user, date=today).update(
            tokens=F("tokens") + tokens,
            images=F("images") + images,
            transcription_seconds=F("transcription_seconds") + transcription_seconds,
            tts_characters=F("tts_characters") + tts_characters,
            vision_requests=F("vision_requests") + vision_requests,
            cost=F("cost") + cost,
        )


class UsageReport:
    """Построение отчётов."""

    @staticmethod
    def spent_in_period(user, kind: str, period_start: datetime) -> int:
        """Сколько единиц ``kind`` потрачено пользователем с ``period_start``."""
        agg_field = {
            "tokens": "total_tokens",
            "images": "units",
            "transcription_seconds": "units",
            "tts_characters": "units",
            "vision": "units",
        }.get(kind, "units")
        kind_enum = {
            "tokens": UsageEvent.Kind.CHAT,
            "images": UsageEvent.Kind.IMAGE,
            "transcription_seconds": UsageEvent.Kind.TRANSCRIPTION,
            "tts_characters": UsageEvent.Kind.TTS,
            "vision": UsageEvent.Kind.VISION,
        }.get(kind)
        if not kind_enum:
            return 0
        qs = UsageEvent.objects.filter(
            user=user, kind=kind_enum, created_at__gte=period_start,
        )
        total = qs.aggregate(value=Sum(agg_field))["value"] or 0
        return int(total)

    @staticmethod
    def summary(user, since: date | None = None) -> dict:
        qs = DailyUsage.objects.filter(user=user)
        if since:
            qs = qs.filter(date__gte=since)
        agg = qs.aggregate(
            tokens=Sum("tokens"),
            images=Sum("images"),
            transcription_seconds=Sum("transcription_seconds"),
            tts_characters=Sum("tts_characters"),
            vision_requests=Sum("vision_requests"),
            cost=Sum("cost"),
        )
        return {key: value or 0 for key, value in agg.items()}
