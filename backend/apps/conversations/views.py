"""View'ы диалогов."""
from __future__ import annotations

from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ai_engine.services import ChatService
from apps.common.permissions import IsOwnerOrAdmin

from .models import Attachment, Conversation, Message
from .serializers import (
    AttachmentSerializer,
    ChatCompletionRequestSerializer,
    ConversationDetailSerializer,
    ConversationSerializer,
    MessageSerializer,
)
from .services import ConversationService


class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrAdmin)
    filterset_fields = ("source", "is_pinned", "is_archived")
    search_fields = ("title", "messages__content")

    def get_queryset(self):
        qs = (
            Conversation.objects.filter(user=self.request.user)
            .annotate(message_count=Count("messages"))
        )
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ConversationDetailSerializer
        return ConversationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def reset(self, request, pk=None):
        conversation = self.get_object()
        ConversationService.reset(conversation)
        return Response({"status": "reset"})

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        conversation = self.get_object()
        conversation.is_archived = True
        conversation.save(update_fields=["is_archived"])
        return Response({"status": "archived"})

    @action(detail=False, methods=["post"], url_path="chat")
    def chat(self, request):
        """Отправляет сообщение в диалог и получает ответ от AI."""
        serializer = ChatCompletionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data.get("conversation_id"):
            conversation = Conversation.objects.get(
                pk=data["conversation_id"], user=request.user,
            )
        else:
            conversation = Conversation.objects.create(
                user=request.user,
                source=Conversation.Source.API,
                model=data.get("model") or request.user.preferences.preferred_model,
            )

        user_message = ConversationService.append_user_message(
            conversation, data["content"],
        )
        result = ChatService().generate_reply(conversation, user_message)
        return Response(
            {
                "conversation": ConversationSerializer(conversation).data,
                "message": MessageSerializer(result.message).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(conversation__user=self.request.user)


class AttachmentViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AttachmentSerializer

    def get_queryset(self):
        return Attachment.objects.filter(message__conversation__user=self.request.user)
