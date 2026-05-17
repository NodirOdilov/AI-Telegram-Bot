"""Админ Telegram-интеграции."""
from __future__ import annotations

from django.contrib import admin

from .models import TelegramCommand, TelegramUpdate


@admin.register(TelegramUpdate)
class TelegramUpdateAdmin(admin.ModelAdmin):
    list_display = ("update_id", "status", "processed_at", "created_at")
    list_filter = ("status",)
    search_fields = ("update_id",)
    readonly_fields = (
        "update_id", "payload", "status",
        "error_message", "processed_at", "created_at", "updated_at",
    )

    def has_add_permission(self, request) -> bool:
        return False


@admin.register(TelegramCommand)
class TelegramCommandAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "requires_admin", "is_visible", "sort_order")
    list_filter = ("requires_admin", "is_visible")
    search_fields = ("code", "description")
