"""Админ-панель биллинга."""
from __future__ import annotations

from django.contrib import admin

from .models import (
    CreditBalance,
    CreditTransaction,
    Invoice,
    Payment,
    Plan,
    Subscription,
)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "price", "billing_period", "is_active", "is_default")
    list_filter = ("billing_period", "is_active", "is_default")
    search_fields = ("code", "name")
    ordering = ("sort_order", "price")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "current_period_end", "autorenew")
    list_filter = ("status", "plan", "autorenew")
    search_fields = ("user__email", "external_id")
    autocomplete_fields = ("user", "plan")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "total", "issued_at", "paid_at")
    list_filter = ("status",)
    search_fields = ("number", "user__email")
    readonly_fields = ("issued_at", "paid_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "provider", "status", "amount", "created_at")
    list_filter = ("provider", "status")
    search_fields = ("external_id", "invoice__number")


@admin.register(CreditBalance)
class CreditBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "lifetime_credited", "lifetime_spent")
    search_fields = ("user__email",)


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "amount", "balance_after", "reason", "created_at")
    list_filter = ("kind",)
    search_fields = ("user__email", "reason", "reference_id")
