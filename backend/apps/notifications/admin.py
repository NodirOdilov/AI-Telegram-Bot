"""Админ уведомлений."""
from __future__ import annotations

from django.contrib import admin

from .models import Broadcast, Notification, NotificationTemplate


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "title", "status", "sent_at")
    list_filter = ("status",)
    search_fields = ("title", "user__email")
    readonly_fields = ("status", "sent_at", "read_at", "error_message")


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "scheduled_at", "sent_count", "failed_count")
    list_filter = ("status",)
    search_fields = ("title",)
