"""Админ-панель плагинов."""
from __future__ import annotations

from django.contrib import admin

from .models import Plugin, PluginConfig, PluginInvocation


@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "version", "is_active", "is_global")
    list_filter = ("is_active", "is_global")
    search_fields = ("code", "name", "description")


@admin.register(PluginConfig)
class PluginConfigAdmin(admin.ModelAdmin):
    list_display = ("user", "plugin", "is_enabled")
    list_filter = ("is_enabled",)
    autocomplete_fields = ("user", "plugin")


@admin.register(PluginInvocation)
class PluginInvocationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "plugin", "status", "duration_ms")
    list_filter = ("status", "plugin")
    search_fields = ("user__email", "plugin__code", "error_message")
    readonly_fields = (
        "user", "plugin", "conversation", "status",
        "arguments", "result", "error_message",
        "duration_ms", "created_at",
    )
