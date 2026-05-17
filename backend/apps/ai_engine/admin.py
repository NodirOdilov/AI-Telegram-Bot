"""Админ AI движка."""
from __future__ import annotations

from django.contrib import admin

from .models import AIModel, AIProvider, AIRequestLog, PromptTemplate


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = (
        "code", "provider", "modality", "is_active", "is_default",
        "context_window", "max_output_tokens",
    )
    list_filter = ("modality", "is_active", "is_default", "provider")
    search_fields = ("code", "name")


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "kind", "language", "is_active")
    list_filter = ("kind", "language", "is_active")
    search_fields = ("code", "name", "content")


@admin.register(AIRequestLog)
class AIRequestLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "provider", "model", "endpoint", "status_code", "duration_ms")
    list_filter = ("provider", "endpoint", "status_code")
    search_fields = ("model", "error_message")
    readonly_fields = (
        "provider", "model", "endpoint",
        "request_payload", "response_payload",
        "status_code", "error_message", "duration_ms", "created_at",
    )

    def has_add_permission(self, request) -> bool:
        return False
