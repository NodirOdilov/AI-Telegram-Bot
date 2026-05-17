"""Сервисный слой биллинга."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import QuotaExceededError

from .models import (
    CreditBalance,
    CreditTransaction,
    Invoice,
    Payment,
    Plan,
    Subscription,
)


@dataclass(slots=True)
class QuotaCheckResult:
    """Результат проверки квоты."""

    allowed: bool
    remaining: int
    quota: int
    reason: str | None = None


class SubscriptionService:
    """Управление подписками."""

    DEFAULT_PERIOD_DAYS = 30

    @classmethod
    @transaction.atomic
    def assign_default_plan(cls, user) -> Subscription:
        """Назначает пользователю тариф по умолчанию."""
        plan = Plan.objects.filter(is_default=True, is_active=True).first()
        if not plan:
            plan = Plan.objects.filter(is_active=True).order_by("price").first()
        if not plan:
            raise RuntimeError("Нет активных тарифов в системе.")
        subscription, _ = Subscription.objects.get_or_create(
            user=user,
            status__in=[Subscription.Status.ACTIVE, Subscription.Status.TRIAL],
            defaults={
                "plan": plan,
                "status": Subscription.Status.ACTIVE,
                "current_period_start": timezone.now(),
                "current_period_end": timezone.now() + timezone.timedelta(days=cls.DEFAULT_PERIOD_DAYS),
            },
        )
        return subscription

    @staticmethod
    @transaction.atomic
    def cancel(subscription: Subscription, immediate: bool = False) -> None:
        subscription.status = Subscription.Status.CANCELLED
        subscription.autorenew = False
        subscription.cancelled_at = timezone.now()
        if immediate:
            subscription.current_period_end = timezone.now()
        subscription.save(update_fields=[
            "status", "autorenew", "cancelled_at", "current_period_end",
        ])

    @staticmethod
    def get_active(user) -> Subscription | None:
        """Возвращает активную подписку пользователя."""
        return (
            Subscription.objects.filter(user=user)
            .filter(status__in=[Subscription.Status.ACTIVE, Subscription.Status.TRIAL])
            .order_by("-current_period_end")
            .first()
        )


class QuotaService:
    """Проверка квот по подписке."""

    QUOTA_FIELDS = {
        "tokens": "token_quota",
        "images": "image_quota",
        "transcription_seconds": "transcription_seconds_quota",
        "tts_characters": "tts_characters_quota",
        "vision": "vision_requests_quota",
    }

    @classmethod
    def check(cls, user, kind: str, amount: int = 1) -> QuotaCheckResult:
        from apps.analytics.services import UsageReport

        subscription = SubscriptionService.get_active(user)
        if subscription is None:
            return QuotaCheckResult(False, 0, 0, "Нет активной подписки")

        field = cls.QUOTA_FIELDS.get(kind)
        if not field:
            return QuotaCheckResult(True, 0, 0)

        quota = getattr(subscription.plan, field, 0)
        if quota == 0:
            # 0 интерпретируется как «безлимит», если в плане так задумано
            return QuotaCheckResult(True, 0, 0)

        spent = UsageReport.spent_in_period(
            user=user,
            kind=kind,
            period_start=subscription.current_period_start,
        )
        remaining = max(0, quota - spent)
        if amount > remaining:
            return QuotaCheckResult(False, remaining, quota, "Квота исчерпана")
        return QuotaCheckResult(True, remaining - amount, quota)

    @classmethod
    def ensure(cls, user, kind: str, amount: int = 1) -> QuotaCheckResult:
        """Проверяет квоту и выбрасывает исключение при превышении."""
        result = cls.check(user, kind, amount)
        if not result.allowed:
            raise QuotaExceededError(result.reason or "Квота исчерпана")
        return result


class CreditService:
    """Управление балансом внутренних кредитов."""

    @classmethod
    @transaction.atomic
    def topup(cls, user, amount: Decimal, reason: str = "", reference=None) -> CreditBalance:
        balance = cls._lock_balance(user)
        balance.balance += amount
        balance.lifetime_credited += amount
        balance.save(update_fields=["balance", "lifetime_credited"])
        CreditTransaction.objects.create(
            user=user,
            kind=CreditTransaction.Kind.TOPUP,
            amount=amount,
            balance_after=balance.balance,
            reason=reason,
            reference_type=reference.__class__.__name__ if reference else "",
            reference_id=str(getattr(reference, "pk", "")) if reference else "",
        )
        return balance

    @classmethod
    @transaction.atomic
    def spend(cls, user, amount: Decimal, reason: str = "", reference=None) -> CreditBalance:
        balance = cls._lock_balance(user)
        if balance.balance < amount:
            raise QuotaExceededError("Недостаточно кредитов на балансе.")
        balance.balance -= amount
        balance.lifetime_spent += amount
        balance.save(update_fields=["balance", "lifetime_spent"])
        CreditTransaction.objects.create(
            user=user,
            kind=CreditTransaction.Kind.SPEND,
            amount=-amount,
            balance_after=balance.balance,
            reason=reason,
            reference_type=reference.__class__.__name__ if reference else "",
            reference_id=str(getattr(reference, "pk", "")) if reference else "",
        )
        return balance

    @staticmethod
    def _lock_balance(user) -> CreditBalance:
        balance, _ = CreditBalance.objects.select_for_update().get_or_create(user=user)
        return balance


class InvoiceService:
    """Генерация и закрытие счетов."""

    @staticmethod
    @transaction.atomic
    def create_for_subscription(subscription: Subscription) -> Invoice:
        plan = subscription.plan
        amount = plan.price
        number = f"INV-{timezone.now():%Y%m}-{uuid.uuid4().hex[:8].upper()}"
        invoice = Invoice.objects.create(
            number=number,
            user=subscription.user,
            subscription=subscription,
            amount=amount,
            total=amount,
            status=Invoice.Status.OPEN,
            due_at=timezone.now() + timezone.timedelta(days=7),
            line_items=[{"name": plan.name, "amount": str(amount.amount)}],
        )
        return invoice

    @staticmethod
    @transaction.atomic
    def mark_paid(invoice: Invoice, payment: Payment | None = None) -> Invoice:
        invoice.status = Invoice.Status.PAID
        invoice.paid_at = timezone.now()
        invoice.save(update_fields=["status", "paid_at"])
        if invoice.subscription:
            sub = invoice.subscription
            sub.current_period_start = timezone.now()
            sub.current_period_end = timezone.now() + timezone.timedelta(days=30)
            sub.status = Subscription.Status.ACTIVE
            sub.save(update_fields=[
                "current_period_start", "current_period_end", "status",
            ])
        return invoice
