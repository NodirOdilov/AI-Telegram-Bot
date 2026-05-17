"""Сериализаторы уведомлений."""
from __future__ import annotations

from rest_framework import serializers

from .models import Broadcast, Notification, NotificationTemplate


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = (
            "id", "status", "sent_at", "read_at", "error_message", "created_at",
        )


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = "__all__"


class BroadcastSerializer(serializers.ModelSerializer):
    class Meta:
        model = Broadcast
        fields = "__all__"
        read_only_fields = (
            "id", "status", "sent_count", "failed_count", "created_at",
        )
