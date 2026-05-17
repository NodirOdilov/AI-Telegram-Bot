"""Админ-панель диалогов."""
from __future__ import annotations

from django.contrib import admin

from .models import Attachment, Conversation, ConversationContext, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = (
        "role", "status", "content", "total_tokens", "cost", "created_at",
    )
    fields = readonly_fields
    can_delete = False
    show_change_link = True


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "source", "model", "last_message_at", "is_pinned", "is_archived")
    list_filter = ("source", "is_pinned", "is_archived", "model")
    search_fields = ("title", "user__email", "external_chat_id")
    autocomplete_fields = ("user",)
    inlines = (MessageInline,)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "status", "total_tokens", "cost", "created_at")
    list_filter = ("role", "status")
    search_fields = ("content", "conversation__title")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("message", "kind", "mime_type", "file_size", "created_at")
    list_filter = ("kind",)


@admin.register(ConversationContext)
class ConversationContextAdmin(admin.ModelAdmin):
    list_display = ("conversation", "last_synced_at")
    search_fields = ("conversation__title",)
