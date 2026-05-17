"""Админ аналитики."""
from __future__ import annotations

from django.contrib import admin

from .models import DailyUsage, SystemMetric, UsageEvent


@admin.register(UsageEvent)
class UsageEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "kind", "model", "total_tokens", "units", "cost")
    list_filter = ("kind", "model")
    search_fields = ("user__email", "model")
    readonly_fields = (
        "user", "kind", "model",
        "prompt_tokens", "completion_tokens", "total_tokens",
        "units", "cost", "conversation", "metadata", "created_at",
    )


@admin.register(DailyUsage)
class DailyUsageAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "tokens", "images", "cost")
    list_filter = ("date",)
    search_fields = ("user__email",)


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "timestamp")
    list_filter = ("key",)
    search_fields = ("key",)
