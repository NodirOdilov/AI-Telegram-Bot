"""Celery задачи приложения conversations."""
from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

from .models import Conversation

logger = logging.getLogger(__name__)


@shared_task(name="apps.conversations.tasks.cleanup_old_conversations")
def cleanup_old_conversations(days: int = 180) -> int:
    """Архивирует и удаляет диалоги старше ``days`` дней."""
    threshold = timezone.now() - timezone.timedelta(days=days)
    qs = Conversation.objects.filter(
        last_message_at__lt=threshold,
        is_archived=False,
    )
    return qs.update(is_archived=True)


@shared_task(name="apps.conversations.tasks.summarise_conversation")
def summarise_conversation(conversation_id: str) -> str:
    """Создаёт краткое содержание длинного диалога для экономии токенов."""
    from apps.ai_engine.services import SummaryService

    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        return ""
    return SummaryService().summarise(conversation)
