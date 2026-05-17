"""Smoke-тесты приложения conversations."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.conversations.models import Conversation
from apps.conversations.services import ConversationService

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_conversation_history_payload():
    user = User.objects.create_user(
        email="test@example.com", password="StrongPass!12345", display_name="Тест",
    )
    conversation = Conversation.objects.create(user=user, source=Conversation.Source.API)
    ConversationService.append_user_message(conversation, "Привет")
    payload = ConversationService.build_history_payload(conversation)
    assert payload[-1]["role"] == "user"
    assert payload[-1]["content"] == "Привет"
