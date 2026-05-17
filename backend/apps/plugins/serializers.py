"""Сериализаторы плагинов."""
from __future__ import annotations

from rest_framework import serializers

from .models import Plugin, PluginConfig, PluginInvocation


class PluginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plugin
        fields = "__all__"


class PluginConfigSerializer(serializers.ModelSerializer):
    plugin = PluginSerializer(read_only=True)
    plugin_id = serializers.PrimaryKeyRelatedField(
        queryset=Plugin.objects.all(), source="plugin", write_only=True,
    )

    class Meta:
        model = PluginConfig
        fields = ("id", "plugin", "plugin_id", "is_enabled", "config",
                  "created_at", "updated_at")


class PluginInvocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PluginInvocation
        fields = "__all__"
