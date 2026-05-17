"""Сериализаторы аналитики."""
from __future__ import annotations

from rest_framework import serializers

from .models import DailyUsage, SystemMetric, UsageEvent


class UsageEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageEvent
        fields = "__all__"


class DailyUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyUsage
        fields = "__all__"


class SystemMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemMetric
        fields = "__all__"


class UsageSummarySerializer(serializers.Serializer):
    tokens = serializers.IntegerField()
    images = serializers.IntegerField()
    transcription_seconds = serializers.IntegerField()
    tts_characters = serializers.IntegerField()
    vision_requests = serializers.IntegerField()
    cost = serializers.DecimalField(max_digits=14, decimal_places=6)
