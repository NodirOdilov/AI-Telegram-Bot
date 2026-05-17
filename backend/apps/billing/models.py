"""Модели биллинга: тарифы, подписки, инвойсы, платежи, кредиты."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import BaseModel, TimeStampedModel


class Plan(BaseModel):
    """Тарифный план."""

    class BillingPeriod(models.TextChoices):
        DAILY = "daily", _("Ежедневно")
        WEEKLY = "weekly", _("Еженедельно")
        MONTHLY = "monthly", _("Ежемесячно")
        YEARLY = "yearly", _("Ежегодно")
        LIFETIME = "lifetime", _("Бессрочно")

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")

    price = MoneyField(max_digits=12, decimal_places=2, default_currency="USD")
    billing_period = models.CharField(
        max_length=16,
        choices=BillingPeriod.choices,
        default=BillingPeriod.MONTHLY,
    )

    # Лимиты тарифа
    token_quota = models.BigIntegerField(default=0, help_text=_("Месячный лимит токенов"))
    image_quota = models.PositiveIntegerField(default=0, help_text=_("Лимит изображений"))
    transcription_seconds_quota = models.PositiveIntegerField(default=0)
    tts_characters_quota = models.PositiveIntegerField(default=0)
    vision_requests_quota = models.PositiveIntegerField(default=0)

    # Включённые функции
    features = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "price")
        verbose_name = _("тарифный план")
        verbose_name_plural = _("тарифные планы")

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if self.is_default:
            Plan.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Subscription(BaseModel):
    """Подписка пользователя на тарифный план."""

    class Status(models.TextChoices):
        TRIAL = "trial", _("Пробный период")
        ACTIVE = "active", _("Активна")
        PAUSED = "paused", _("Приостановлена")
        CANCELLED = "cancelled", _("Отменена")
        EXPIRED = "expired", _("Истекла")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    started_at = models.DateTimeField(default=timezone.now)
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    autorenew = models.BooleanField(default=True)

    external_id = models.CharField(max_length=128, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("подписка")
        verbose_name_plural = _("подписки")
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["current_period_end"]),
        ]

    def is_active(self) -> bool:
        if self.status not in (self.Status.ACTIVE, self.Status.TRIAL):
            return False
        if self.current_period_end and self.current_period_end < timezone.now():
            return False
        return True


class Invoice(BaseModel):
    """Счёт на оплату."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Черновик")
        OPEN = "open", _("Ожидает оплаты")
        PAID = "paid", _("Оплачен")
        VOID = "void", _("Аннулирован")
        REFUNDED = "refunded", _("Возврат")

    number = models.CharField(max_length=32, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        related_name="invoices",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    amount = MoneyField(max_digits=12, decimal_places=2, default_currency="USD")
    tax = MoneyField(max_digits=12, decimal_places=2, default_currency="USD",
                     default=Decimal("0"))
    total = MoneyField(max_digits=12, decimal_places=2, default_currency="USD")

    issued_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    line_items = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = _("счёт")
        verbose_name_plural = _("счета")
        ordering = ("-issued_at",)


class Payment(BaseModel):
    """Финансовая транзакция (платёж по счёту)."""

    class Provider(models.TextChoices):
        STRIPE = "stripe", _("Stripe")
        TELEGRAM = "telegram", _("Telegram Payments")
        MANUAL = "manual", _("Ручной перевод")
        INTERNAL = "internal", _("Внутренний баланс")

    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает")
        SUCCESS = "success", _("Успешно")
        FAILED = "failed", _("Ошибка")
        REFUNDED = "refunded", _("Возврат")

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    provider = models.CharField(max_length=16, choices=Provider.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    amount = MoneyField(max_digits=12, decimal_places=2, default_currency="USD")

    external_id = models.CharField(max_length=128, blank=True, default="")
    raw_payload = models.JSONField(default=dict, blank=True)

    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("платёж")
        verbose_name_plural = _("платежи")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["provider", "external_id"]),
        ]


class CreditBalance(TimeStampedModel):
    """Кошелёк пользователя в кредитах (внутренней валюте)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_balance",
    )
    balance = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0"))
    lifetime_credited = models.DecimalField(
        max_digits=14, decimal_places=4, default=Decimal("0"),
    )
    lifetime_spent = models.DecimalField(
        max_digits=14, decimal_places=4, default=Decimal("0"),
    )

    class Meta:
        verbose_name = _("баланс кредитов")
        verbose_name_plural = _("балансы кредитов")


class CreditTransaction(TimeStampedModel):
    """Запись об изменении баланса кредитов."""

    class Kind(models.TextChoices):
        TOPUP = "topup", _("Пополнение")
        SPEND = "spend", _("Списание")
        REFUND = "refund", _("Возврат")
        BONUS = "bonus", _("Бонус")
        ADJUSTMENT = "adjustment", _("Корректировка")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_transactions",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=4)
    balance_after = models.DecimalField(max_digits=14, decimal_places=4)
    reason = models.CharField(max_length=255, blank=True, default="")
    reference_type = models.CharField(max_length=64, blank=True, default="")
    reference_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]
