"""Сервисный слой Telegram-бота.

Содержит:
* ``TelegramSender`` — упрощённый клиент Bot API для отправки сообщений.
* ``UpdateRouter`` — маршрутизатор входящих обновлений (webhook).
* ``CommandHandlerRegistry`` — реестр обработчиков команд.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any, Callable

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.ai_engine.services import ChatService, ImageService, TranscriptionService, TTSService
from apps.common.exceptions import QuotaExceededError
from apps.conversations.models import Conversation
from apps.conversations.services import ConversationService

from .models import TelegramUpdate

logger = logging.getLogger(__name__)
User = get_user_model()


@dataclass(slots=True)
class TelegramContext:
    """Контекст обработчика."""

    update: dict
    chat_id: int
    user_id: int
    text: str
    user: Any
    is_voice: bool = False
    voice_file_id: str | None = None
    photo_file_id: str | None = None


class TelegramSender:
    """Минимальный синхронный клиент Telegram Bot API."""

    API_BASE = "https://api.telegram.org/bot{token}/{method}"
    FILE_BASE = "https://api.telegram.org/file/bot{token}/{path}"

    def __init__(self, token: str | None = None) -> None:
        self.token = token or settings.TELEGRAM_BOT_TOKEN

    def _call(self, method: str, **payload) -> dict:
        if not self.token:
            logger.warning("Telegram токен не задан, метод %s не вызван.", method)
            return {}
        url = self.API_BASE.format(token=self.token, method=method)
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code >= 400:
            logger.error("Telegram %s: %s", method, response.text)
        return response.json() if response.content else {}

    def send_text(self, chat_id: int, text: str, parse_mode: str | None = None,
                  reply_markup: dict | None = None) -> dict:
        payload: dict = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return self._call("sendMessage", **payload)

    def send_photo(self, chat_id: int, photo_url: str, caption: str = "") -> dict:
        return self._call("sendPhoto", chat_id=chat_id, photo=photo_url, caption=caption)

    def send_voice(self, chat_id: int, audio_bytes: bytes, mime_type: str = "audio/mpeg") -> dict:
        if not self.token:
            return {}
        url = self.API_BASE.format(token=self.token, method="sendVoice")
        files = {"voice": ("voice.mp3", io.BytesIO(audio_bytes), mime_type)}
        return requests.post(url, data={"chat_id": chat_id}, files=files, timeout=60).json()

    def set_webhook(self, url: str, secret_token: str | None = None) -> dict:
        payload: dict = {"url": url}
        if secret_token:
            payload["secret_token"] = secret_token
        return self._call("setWebhook", **payload)

    def delete_webhook(self) -> dict:
        return self._call("deleteWebhook", drop_pending_updates=True)

    def download_file(self, file_id: str) -> bytes:
        info = self._call("getFile", file_id=file_id)
        path = info.get("result", {}).get("file_path")
        if not path or not self.token:
            return b""
        url = self.FILE_BASE.format(token=self.token, path=path)
        return requests.get(url, timeout=60).content


class CommandHandlerRegistry:
    """Реестр обработчиков команд бота."""

    _registry: dict[str, Callable[[TelegramContext], None]] = {}

    @classmethod
    def register(cls, code: str):
        def wrapper(func: Callable[[TelegramContext], None]):
            cls._registry[code] = func
            return func
        return wrapper

    @classmethod
    def dispatch(cls, ctx: TelegramContext) -> bool:
        command = (ctx.text or "").split()[0].lstrip("/").split("@")[0]
        handler = cls._registry.get(command)
        if handler is None:
            return False
        handler(ctx)
        return True


@CommandHandlerRegistry.register("start")
def handle_start(ctx: TelegramContext) -> None:
    TelegramSender().send_text(
        ctx.chat_id,
        "Здравствуйте! Я AI-ассистент. Задайте мне вопрос текстом или голосом.",
    )


@CommandHandlerRegistry.register("reset")
def handle_reset(ctx: TelegramContext) -> None:
    conversation = ConversationService.get_or_create_for_chat(
        ctx.user, str(ctx.chat_id), Conversation.Source.TELEGRAM,
    )
    ConversationService.reset(conversation)
    TelegramSender().send_text(ctx.chat_id, "История диалога очищена.")


@CommandHandlerRegistry.register("help")
def handle_help(ctx: TelegramContext) -> None:
    TelegramSender().send_text(
        ctx.chat_id,
        "Доступные команды:\n"
        "/start — начало работы\n"
        "/reset — очистить диалог\n"
        "/image <описание> — сгенерировать изображение\n"
        "/voice — ответ голосом\n"
        "/help — справка",
    )


@CommandHandlerRegistry.register("image")
def handle_image(ctx: TelegramContext) -> None:
    parts = ctx.text.split(maxsplit=1)
    prompt = parts[1] if len(parts) > 1 else ""
    if not prompt:
        TelegramSender().send_text(ctx.chat_id, "Укажите описание изображения после /image.")
        return
    try:
        response = ImageService().generate(ctx.user, prompt)
    except QuotaExceededError as exc:
        TelegramSender().send_text(ctx.chat_id, f"Квота исчерпана: {exc}")
        return
    TelegramSender().send_photo(ctx.chat_id, response.url, caption=response.revised_prompt[:1024])


class UpdateRouter:
    """Главный маршрутизатор входящих обновлений."""

    @classmethod
    def handle(cls, payload: dict) -> None:
        update_id = payload.get("update_id")
        if update_id is None:
            return
        record, created = TelegramUpdate.objects.get_or_create(
            update_id=update_id,
            defaults={"payload": payload},
        )
        if not created:
            return  # идемпотентность

        record.status = TelegramUpdate.Status.PROCESSING
        record.save(update_fields=["status"])

        try:
            cls._dispatch(payload)
            record.status = TelegramUpdate.Status.PROCESSED
            record.processed_at = timezone.now()
            record.save(update_fields=["status", "processed_at"])
        except Exception as exc:
            logger.exception("Ошибка обработки обновления %s", update_id)
            record.status = TelegramUpdate.Status.FAILED
            record.error_message = str(exc)
            record.save(update_fields=["status", "error_message"])

    @classmethod
    def _dispatch(cls, payload: dict) -> None:
        message = payload.get("message") or payload.get("edited_message")
        if not message:
            return

        chat = message.get("chat", {})
        sender = message.get("from", {})
        chat_id = chat.get("id")
        user_id = sender.get("id")
        if not chat_id or not user_id:
            return

        # Проверка allow-list пользователей
        allowed = settings.TELEGRAM_ALLOWED_IDS
        if allowed and "*" not in allowed and str(user_id) not in allowed:
            TelegramSender().send_text(chat_id, "Доступ ограничен. Обратитесь к администратору.")
            return

        user, _ = User.objects.get_or_create_telegram_user(
            telegram_id=user_id,
            username=sender.get("username") or "",
            first_name=sender.get("first_name") or "",
            last_name=sender.get("last_name") or "",
            language_code=sender.get("language_code") or "ru",
        )

        # Обновляем chat_id для последующих push-уведомлений
        if user.telegram_profile.chat_id != chat_id:
            user.telegram_profile.chat_id = chat_id
            user.telegram_profile.save(update_fields=["chat_id"])
        user.telegram_profile.touch()

        text = message.get("text") or message.get("caption") or ""
        voice = message.get("voice") or message.get("audio")
        photo = message.get("photo")

        ctx = TelegramContext(
            update=payload,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            user=user,
            is_voice=bool(voice),
            voice_file_id=voice.get("file_id") if voice else None,
            photo_file_id=photo[-1]["file_id"] if photo else None,
        )

        # Голосовое сообщение -> расшифровка
        if ctx.is_voice and ctx.voice_file_id:
            audio_bytes = TelegramSender().download_file(ctx.voice_file_id)
            try:
                transcription = TranscriptionService().transcribe(
                    user, audio_bytes, filename="voice.ogg",
                )
                ctx.text = transcription.text
            except QuotaExceededError as exc:
                TelegramSender().send_text(chat_id, f"Квота исчерпана: {exc}")
                return

        # Команды начинаются с "/"
        if ctx.text.startswith("/"):
            if CommandHandlerRegistry.dispatch(ctx):
                return

        if not ctx.text:
            TelegramSender().send_text(chat_id, "Отправьте текстовое или голосовое сообщение.")
            return

        cls._handle_chat(ctx)

    @staticmethod
    def _handle_chat(ctx: TelegramContext) -> None:
        sender = TelegramSender()
        conversation = ConversationService.get_or_create_for_chat(
            ctx.user, str(ctx.chat_id), Conversation.Source.TELEGRAM,
        )
        user_message = ConversationService.append_user_message(
            conversation, ctx.text,
            external_message_id=str(ctx.update.get("message", {}).get("message_id", "")),
        )
        try:
            result = ChatService().generate_reply(conversation, user_message)
        except QuotaExceededError as exc:
            sender.send_text(ctx.chat_id, f"Квота исчерпана: {exc}")
            return
        except Exception as exc:
            logger.exception("Ошибка генерации ответа AI")
            sender.send_text(ctx.chat_id, "Произошла ошибка при обращении к AI. Попробуйте позже.")
            return

        reply_text = result.message.content or "Не удалось получить ответ."
        prefs = getattr(ctx.user, "preferences", None)
        if prefs and prefs.voice_only:
            tts = TTSService().synthesize(ctx.user, reply_text, voice=prefs.tts_voice)
            sender.send_voice(ctx.chat_id, tts.audio_bytes)
        else:
            sender.send_text(ctx.chat_id, reply_text)
