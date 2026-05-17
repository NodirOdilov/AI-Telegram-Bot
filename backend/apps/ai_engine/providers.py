"""Адаптеры провайдеров AI: OpenAI, Anthropic, Google.

Все провайдеры реализуют общий интерфейс ``BaseProvider``.
Реальные вызовы делаются через официальные SDK; при отсутствии ключей
адаптеры возвращают заглушки, что позволяет работать в локальной среде.
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChatResponse:
    """Результат одного chat completion."""

    content: str
    prompt_tokens: int
    completion_tokens: int
    raw: dict
    cost: Decimal = Decimal("0")


@dataclass(slots=True)
class ImageResponse:
    """Результат генерации изображения."""

    url: str
    revised_prompt: str
    raw: dict


@dataclass(slots=True)
class TranscriptionResponse:
    text: str
    language: str
    raw: dict


@dataclass(slots=True)
class SpeechResponse:
    audio_bytes: bytes
    mime_type: str
    duration_seconds: float


class BaseProvider(ABC):
    """Абстрактный поставщик AI."""

    code: str = "base"

    @abstractmethod
    def chat(self, messages: list[dict], **params) -> ChatResponse:
        ...

    def stream_chat(self, messages: list[dict], **params) -> Iterable[str]:
        """Потоковая генерация. По умолчанию делается обычный chat."""
        response = self.chat(messages, **params)
        yield response.content

    def generate_image(self, prompt: str, **params) -> ImageResponse:
        raise NotImplementedError

    def transcribe(self, audio: bytes, **params) -> TranscriptionResponse:
        raise NotImplementedError

    def synthesize_speech(self, text: str, **params) -> SpeechResponse:
        raise NotImplementedError


class OpenAIProvider(BaseProvider):
    """Адаптер OpenAI."""

    code = "openai"

    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY or "sk-empty",
            base_url=settings.OPENAI_BASE_URL,
        )

    def chat(self, messages: list[dict], **params) -> ChatResponse:
        model = params.pop("model", settings.OPENAI_MODEL)
        start = time.perf_counter()
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **params,
        )
        elapsed = (time.perf_counter() - start) * 1000
        choice = response.choices[0]
        usage = response.usage
        logger.info(
            "OpenAI chat model=%s tokens_in=%s tokens_out=%s latency=%.0fмс",
            model, usage.prompt_tokens, usage.completion_tokens, elapsed,
        )
        return ChatResponse(
            content=choice.message.content or "",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            raw=response.model_dump(),
        )

    def stream_chat(self, messages: list[dict], **params) -> Iterable[str]:
        model = params.pop("model", settings.OPENAI_MODEL)
        params["stream"] = True
        stream = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **params,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def generate_image(self, prompt: str, **params) -> ImageResponse:
        model = params.pop("model", settings.OPENAI_IMAGE_MODEL)
        response = self.client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            **params,
        )
        item = response.data[0]
        return ImageResponse(
            url=item.url or "",
            revised_prompt=getattr(item, "revised_prompt", "") or prompt,
            raw=response.model_dump(),
        )

    def transcribe(self, audio: bytes, **params) -> TranscriptionResponse:
        import io

        model = params.pop("model", settings.OPENAI_WHISPER_MODEL)
        buffer = io.BytesIO(audio)
        buffer.name = params.pop("filename", "audio.ogg")
        response = self.client.audio.transcriptions.create(
            file=buffer, model=model,
            response_format="verbose_json",
            **params,
        )
        return TranscriptionResponse(
            text=response.text,
            language=getattr(response, "language", "ru"),
            raw=response.model_dump(),
        )

    def synthesize_speech(self, text: str, **params) -> SpeechResponse:
        model = params.pop("model", settings.OPENAI_TTS_MODEL)
        voice = params.pop("voice", "alloy")
        response = self.client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            **params,
        )
        audio_bytes = response.read() if hasattr(response, "read") else response.content
        return SpeechResponse(
            audio_bytes=audio_bytes,
            mime_type="audio/mpeg",
            duration_seconds=len(text) / 15.0,  # эмпирическая оценка
        )


class AnthropicProvider(BaseProvider):
    """Адаптер Anthropic Claude."""

    code = "anthropic"

    def __init__(self) -> None:
        import anthropic

        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY or "sk-empty")

    def chat(self, messages: list[dict], **params) -> ChatResponse:
        model = params.pop("model", "claude-opus-4-7")
        system = ""
        anthropic_messages: list[dict[str, Any]] = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})
        max_tokens = params.pop("max_tokens", 4096)
        response = self.client.messages.create(
            model=model,
            system=system or "Вы — полезный ассистент.",
            messages=anthropic_messages,
            max_tokens=max_tokens,
            **{k: v for k, v in params.items() if k not in ("stream",)},
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        usage = response.usage
        return ChatResponse(
            content=text,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            raw=response.model_dump(),
        )


class ProviderRegistry:
    """Реестр доступных провайдеров."""

    _instances: dict[str, BaseProvider] = {}

    @classmethod
    def get(cls, code: str) -> BaseProvider:
        if code in cls._instances:
            return cls._instances[code]
        if code == "openai":
            cls._instances[code] = OpenAIProvider()
        elif code == "anthropic":
            cls._instances[code] = AnthropicProvider()
        else:
            raise ValueError(f"Неизвестный провайдер: {code}")
        return cls._instances[code]

    @classmethod
    def for_model(cls, model_code: str) -> BaseProvider:
        """Определяет провайдера по идентификатору модели."""
        if model_code.startswith("claude"):
            return cls.get("anthropic")
        return cls.get("openai")
