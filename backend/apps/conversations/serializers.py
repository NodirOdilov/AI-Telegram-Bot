"""DRF сериализаторы диалогов."""
from __future__ import annotations

from rest_framework import serializers

from .models import Attachment, Conversation, Message


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class MessageSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = (
            "id", "conversation", "role", "content", "status",
            "tool_name", "tool_arguments", "tool_response",
            "prompt_tokens", "completion_tokens", "total_tokens", "cost",
            "external_message_id", "reply_to", "metadata",
            "attachments", "created_at",
        )
        read_only_fields = (
            "id", "status",
            "prompt_tokens", "completion_tokens", "total_tokens", "cost",
            "attachments", "created_at",
        )


class ConversationSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id", "title", "source", "model", "system_prompt",
            "external_chat_id", "last_message_at",
            "is_pinned", "is_archived",
            "metadata", "message_count", "created_at",
        )
        read_only_fields = (
            "id", "last_message_at", "message_count", "created_at",
        )


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ("messages",)


class ChatCompletionRequestSerializer(serializers.Serializer):
    """Запрос на генерацию ответа в диалоге."""

    conversation_id = serializers.UUIDField(required=False)
    content = serializers.CharField()
    stream = serializers.BooleanField(default=False)
    model = serializers.CharField(required=False, allow_blank=True)
    attachments = serializers.ListField(child=serializers.URLField(), required=False)
