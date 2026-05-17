"""DRF сериализаторы биллинга."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    CreditBalance,
    CreditTransaction,
    Invoice,
    Payment,
    Plan,
    Subscription,
)


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(), source="plan", write_only=True,
    )

    class Meta:
        model = Subscription
        fields = (
            "id", "plan", "plan_id", "status",
            "started_at", "current_period_start", "current_period_end",
            "cancelled_at", "autorenew", "metadata",
        )
        read_only_fields = (
            "id", "status", "started_at",
            "current_period_start", "current_period_end", "cancelled_at",
        )


class InvoiceSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, source="amount.amount")
    total = serializers.DecimalField(max_digits=12, decimal_places=2, source="total.amount")
    currency = serializers.CharField(source="amount_currency", read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id", "number", "user", "subscription", "status",
            "amount", "tax", "total", "currency",
            "issued_at", "due_at", "paid_at", "line_items",
        )
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = (
            "id", "status", "processed_at", "raw_payload", "created_at",
        )


class CreditBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditBalance
        fields = ("balance", "lifetime_credited", "lifetime_spent", "updated_at")


class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = "__all__"
