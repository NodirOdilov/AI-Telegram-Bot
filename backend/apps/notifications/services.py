"""Сервисный слой уведомлений."""
from __future__ import annotations

import logging
from typing import Iterable

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)


class NotificationChannel:
    """Базовый канал доставки."""

    code: str = "base"

    def send(self, user, title: str, body: str, payload: dict) -> None:
        raise NotImplementedError


class EmailChannel(NotificationChannel):
    code = "email"

    def send(self, user, title: str, body: str, payload: dict) -> None:
        if not user.email:
            raise ValueError("У пользователя нет email-адреса.")
        send_mail(
            subject=title,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )


class TelegramChannel(NotificationChannel):
    code = "telegram"

    def send(self, user, title: str, body: str, payload: dict) -> None:
        from apps.telegram_bot.services import TelegramSender

        profile = getattr(user, "telegram_profile", None)
        if not profile or not profile.chat_id:
            raise ValueError("У пользователя нет Telegram-чата.")
        message = f"<b>{title}</b>\n\n{body}"
        TelegramSender().send_text(profile.chat_id, message, parse_mode="HTML")


class WebSocketChannel(NotificationChannel):
    code = "websocket"

    def send(self, user, title: str, body: str, payload: dict) -> None:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if layer is None:
            return
        async_to_sync(layer.group_send)(
            f"user.{user.id}",
            {
                "type": "notification.message",
                "title": title,
                "body": body,
                "payload": payload,
            },
        )


CHANNEL_REGISTRY: dict[str, NotificationChannel] = {
    "email": EmailChannel(),
    "telegram": TelegramChannel(),
    "websocket": WebSocketChannel(),
}


class NotificationService:
    """Универсальный отправитель уведомлений."""

    @classmethod
    def send(
        cls,
        user,
        title: str,
        body: str,
        payload: dict | None = None,
        channels: Iterable[str] = ("websocket",),
    ) -> Notification:
        notification = Notification.objects.create(
            user=user,
            title=title,
            body=body,
            payload=payload or {},
            channels=list(channels),
        )
        errors: list[str] = []
        for channel_code in channels:
            channel = CHANNEL_REGISTRY.get(channel_code)
            if not channel:
                errors.append(f"Канал {channel_code} не найден")
                continue
            try:
                channel.send(user, title, body, payload or {})
            except Exception as exc:
                logger.exception("Ошибка отправки через %s", channel_code)
                errors.append(f"{channel_code}: {exc}")

        if errors:
            notification.status = Notification.Status.FAILED
            notification.error_message = "; ".join(errors)
        else:
            notification.status = Notification.Status.SENT
            notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at", "error_message"])
        return notification
