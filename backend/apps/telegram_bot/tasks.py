"""Celery задачи Telegram-бота."""
from __future__ import annotations

import logging

from celery import shared_task

from .services import TelegramSender, UpdateRouter

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.telegram_bot.tasks.process_telegram_update",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_telegram_update(payload: dict) -> bool:
    """Обрабатывает входящее обновление Telegram."""
    UpdateRouter.handle(payload)
    return True


@shared_task(name="apps.telegram_bot.tasks.broadcast_message")
def broadcast_message(chat_ids: list[int], text: str) -> int:
    """Рассылает текстовое сообщение списку чатов."""
    sender = TelegramSender()
    delivered = 0
    for chat_id in chat_ids:
        try:
            sender.send_text(chat_id, text)
            delivered += 1
        except Exception:
            logger.exception("Не удалось отправить сообщение в чат %s", chat_id)
    return delivered
