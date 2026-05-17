"""Сервисный слой для диалогов."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import Conversation, ConversationContext, Message

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CompletionResult:
    """Результат генерации ответа AI."""

    message: Message
    raw_response: dict


class ConversationService:
    """Высокоуровневые операции над диалогами."""

    MAX_HISTORY = 30

    @staticmethod
    @transaction.atomic
    def get_or_create_for_chat(
        user,
        external_chat_id: str,
        source: str,
        title: str | None = None,
    ) -> Conversation:
        conversation, created = Conversation.objects.get_or_create(
            user=user,
            external_chat_id=external_chat_id,
            source=source,
            is_archived=False,
            defaults={"title": title or ""},
        )
        return conversation

    @staticmethod
    @transaction.atomic
    def append_user_message(
        conversation: Conversation,
        content: str,
        *,
        external_message_id: str = "",
        metadata: dict | None = None,
    ) -> Message:
        message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content=content,
            external_message_id=external_message_id,
            metadata=metadata or {},
            status=Message.Status.COMPLETED,
        )
        Conversation.objects.filter(pk=conversation.pk).update(
            last_message_at=timezone.now(),
        )
        return message

    @staticmethod
    @transaction.atomic
    def append_assistant_message(
        conversation: Conversation,
        content: str,
        *,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: Decimal | None = None,
        reply_to: Message | None = None,
        metadata: dict | None = None,
    ) -> Message:
        message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost or Decimal("0"),
            reply_to=reply_to,
            metadata=metadata or {},
            status=Message.Status.COMPLETED,
        )
        Conversation.objects.filter(pk=conversation.pk).update(
            last_message_at=timezone.now(),
        )
        return message

    @classmethod
    def build_history_payload(cls, conversation: Conversation) -> list[dict]:
        """Формирует историю сообщений в формате OpenAI Chat Completion."""
        messages: list[dict] = []
        if conversation.system_prompt:
            messages.append({"role": "system", "content": conversation.system_prompt})

        # Если есть сводка контекста, добавляем её в начало
        try:
            ctx = conversation.context
            if ctx and ctx.summary:
                messages.append({
                    "role": "system",
                    "content": f"Сводка предыдущего разговора: {ctx.summary}",
                })
        except ConversationContext.DoesNotExist:
            pass

        qs = (
            conversation.messages
            .filter(status=Message.Status.COMPLETED)
            .order_by("-created_at")[: cls.MAX_HISTORY]
        )
        for msg in reversed(list(qs)):
            messages.append({"role": msg.role, "content": msg.content})
        return messages

    @staticmethod
    @transaction.atomic
    def reset(conversation: Conversation) -> None:
        """Полностью очищает историю диалога."""
        conversation.messages.all().delete()
        ConversationContext.objects.filter(conversation=conversation).delete()
        Conversation.objects.filter(pk=conversation.pk).update(last_message_at=None)
