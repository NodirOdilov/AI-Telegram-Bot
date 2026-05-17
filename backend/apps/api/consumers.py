"""WebSocket-консьюмеры на базе Django Channels.

* ``ChatConsumer`` — двусторонний обмен сообщениями в диалоге, поддерживает
  стриминг ответа AI по чанкам.
* ``NotificationConsumer`` — персональный канал для push-уведомлений.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """Стриминговый чат через WebSocket."""

    async def connect(self) -> None:
        user = self.scope.get("user")
        if not user or isinstance(user, AnonymousUser):
            await self.close(code=4401)
            return

        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"chat.{self.conversation_id}"

        # Проверяем, что диалог принадлежит пользователю
        ok = await self._user_owns_conversation(user, self.conversation_id)
        if not ok:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "ready"})

    async def disconnect(self, code: int) -> None:
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content: dict, **kwargs) -> None:
        action = content.get("action")
        if action == "ping":
            await self.send_json({"type": "pong"})
            return
        if action == "send":
            text = content.get("text", "")
            await self._handle_send(text)

    async def chat_message(self, event: dict) -> None:
        """Получает сообщение от group_send и отправляет его клиенту."""
        await self.send_json({"type": "message", "payload": event.get("payload", {})})

    async def chat_chunk(self, event: dict) -> None:
        await self.send_json({"type": "chunk", "delta": event.get("delta", "")})

    async def _handle_send(self, text: str) -> None:
        from apps.ai_engine.services import ChatService
        from apps.conversations.models import Conversation
        from apps.conversations.services import ConversationService

        user = self.scope["user"]
        conversation = await sync_to_async(
            lambda: Conversation.objects.get(pk=self.conversation_id, user=user)
        )()
        user_message = await sync_to_async(ConversationService.append_user_message)(
            conversation, text,
        )
        # Простейший вариант: синхронный ответ + единичный чанк
        result = await sync_to_async(ChatService().generate_reply)(conversation, user_message)
        await self.send_json({
            "type": "message",
            "payload": {
                "id": str(result.message.id),
                "content": result.message.content,
                "tokens": result.message.total_tokens,
            },
        })

    @staticmethod
    async def _user_owns_conversation(user, conversation_id) -> bool:
        from apps.conversations.models import Conversation
        return await sync_to_async(
            Conversation.objects.filter(pk=conversation_id, user=user).exists
        )()


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Персональный канал для push-уведомлений."""

    async def connect(self) -> None:
        user = self.scope.get("user")
        if not user or isinstance(user, AnonymousUser):
            await self.close(code=4401)
            return
        self.group_name = f"user.{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_message(self, event: dict) -> None:
        await self.send_json({
            "type": "notification",
            "title": event.get("title", ""),
            "body": event.get("body", ""),
            "payload": event.get("payload", {}),
        })
