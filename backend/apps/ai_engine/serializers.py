"""Сериализаторы AI движка."""
from __future__ import annotations

from rest_framework import serializers

from .models import AIModel, AIProvider, AIRequestLog, PromptTemplate


class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = "__all__"


class AIModelSerializer(serializers.ModelSerializer):
    provider = AIProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=AIProvider.objects.all(), source="provider", write_only=True,
    )

    class Meta:
        model = AIModel
        fields = "__all__"


class PromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = "__all__"


class AIRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRequestLog
        fields = "__all__"
