"""Высокоуровневые сервисы AI движка."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from django.conf import settings
from django.utils import timezone

from apps.billing.services import QuotaService
from apps.conversations.models import Conversation, Message
from apps.conversations.services import CompletionResult, ConversationService

from .models import AIModel, AIRequestLog
from .providers import ChatResponse, ImageResponse, ProviderRegistry

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CostBreakdown:
    """Оценка стоимости запроса."""

    input_cost: Decimal
    output_cost: Decimal
    total: Decimal


class CostCalculator:
    """Расчёт стоимости запросов в провайдеры."""

    @staticmethod
    def for_chat(model_code: str, prompt_tokens: int, completion_tokens: int) -> CostBreakdown:
        ai_model = AIModel.objects.filter(code=model_code).first()
        if not ai_model:
            return CostBreakdown(Decimal("0"), Decimal("0"), Decimal("0"))
        input_cost = Decimal(prompt_tokens) * ai_model.input_token_price / Decimal("1000")
        output_cost = Decimal(completion_tokens) * ai_model.output_token_price / Decimal("1000")
        return CostBreakdown(input_cost, output_cost, input_cost + output_cost)

    @staticmethod
    def for_image(model_code: str) -> Decimal:
        ai_model = AIModel.objects.filter(code=model_code).first()
        return ai_model.image_price if ai_model else Decimal("0")


class ChatService:
    """Генерация ответов AI в диалоге."""

    def generate_reply(
        self,
        conversation: Conversation,
        user_message: Message,
    ) -> CompletionResult:
        QuotaService.ensure(conversation.user, "tokens", amount=1)

        history = ConversationService.build_history_payload(conversation)
        provider = ProviderRegistry.for_model(conversation.model or settings.OPENAI_MODEL)

        prefs = getattr(conversation.user, "preferences", None)
        params = {
            "model": conversation.model or settings.OPENAI_MODEL,
            "temperature": float(prefs.temperature) if prefs else 1.0,
            "max_tokens": prefs.max_tokens if prefs else 1200,
        }

        response = self._call(provider, history, params)
        cost = CostCalculator.for_chat(
            params["model"], response.prompt_tokens, response.completion_tokens,
        )
        message = ConversationService.append_assistant_message(
            conversation,
            response.content,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            cost=cost.total,
            reply_to=user_message,
            metadata={"provider": provider.code, "params": params},
        )

        # Запись в аналитику
        from apps.analytics.services import UsageRecorder
        UsageRecorder.record_chat(
            user=conversation.user,
            model=params["model"],
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            cost=cost.total,
            conversation=conversation,
        )

        return CompletionResult(message=message, raw_response=response.raw)

    def stream_reply(
        self,
        conversation: Conversation,
        user_message: Message,
    ) -> Iterable[str]:
        QuotaService.ensure(conversation.user, "tokens")
        history = ConversationService.build_history_payload(conversation)
        provider = ProviderRegistry.for_model(conversation.model or settings.OPENAI_MODEL)
        for chunk in provider.stream_chat(history, model=conversation.model or settings.OPENAI_MODEL):
            yield chunk

    @staticmethod
    def _call(provider, history: list[dict], params: dict) -> ChatResponse:
        import time

        start = time.perf_counter()
        try:
            response = provider.chat(history, **params)
            AIRequestLog.objects.create(
                provider=provider.code,
                model=params.get("model", ""),
                endpoint="chat",
                request_payload={"messages": history, "params": params},
                response_payload=response.raw,
                status_code=200,
                duration_ms=int((time.perf_counter() - start) * 1000),
            )
            return response
        except Exception as exc:
            logger.exception("Ошибка вызова провайдера %s", provider.code)
            AIRequestLog.objects.create(
                provider=provider.code,
                model=params.get("model", ""),
                endpoint="chat",
                request_payload={"messages": history, "params": params},
                response_payload={},
                status_code=500,
                error_message=str(exc),
                duration_ms=int((time.perf_counter() - start) * 1000),
            )
            raise


class ImageService:
    """Генерация изображений."""

    def generate(self, user, prompt: str, **params) -> ImageResponse:
        QuotaService.ensure(user, "images")
        provider = ProviderRegistry.get("openai")
        response = provider.generate_image(prompt, **params)
        from apps.analytics.services import UsageRecorder
        UsageRecorder.record_image(
            user=user,
            model=params.get("model", settings.OPENAI_IMAGE_MODEL),
            prompt=prompt,
            cost=CostCalculator.for_image(
                params.get("model", settings.OPENAI_IMAGE_MODEL),
            ),
        )
        return response


class TranscriptionService:
    """Распознавание речи."""

    def transcribe(self, user, audio: bytes, filename: str = "audio.ogg", **params):
        QuotaService.ensure(user, "transcription_seconds")
        provider = ProviderRegistry.get("openai")
        response = provider.transcribe(audio, filename=filename, **params)
        from apps.analytics.services import UsageRecorder
        UsageRecorder.record_transcription(user=user, duration=len(audio) / 16000)
        return response


class TTSService:
    """Синтез речи."""

    def synthesize(self, user, text: str, voice: str = "alloy", **params):
        QuotaService.ensure(user, "tts_characters", amount=len(text))
        provider = ProviderRegistry.get("openai")
        response = provider.synthesize_speech(text, voice=voice, **params)
        from apps.analytics.services import UsageRecorder
        UsageRecorder.record_tts(user=user, characters=len(text))
        return response


class SummaryService:
    """Сжимает длинные диалоги в сводку для экономии токенов."""

    def summarise(self, conversation: Conversation) -> str:
        from apps.conversations.models import ConversationContext

        history = ConversationService.build_history_payload(conversation)
        prompt = (
            "Ниже приведён фрагмент диалога. "
            "Сформируйте краткое резюме на русском языке, "
            "сохраняя ключевые факты и контекст:\n\n"
            + "\n".join(f"{m['role']}: {m['content']}" for m in history)
        )
        provider = ProviderRegistry.get("openai")
        response = provider.chat(
            [{"role": "user", "content": prompt}],
            model=settings.OPENAI_MODEL,
            temperature=0.2,
            max_tokens=512,
        )
        summary = response.content
        ConversationContext.objects.update_or_create(
            conversation=conversation,
            defaults={"summary": summary, "last_synced_at": timezone.now()},
        )
        return summary
