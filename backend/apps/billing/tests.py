"""Smoke-тесты биллинга."""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.billing.models import Plan
from apps.billing.services import CreditService, SubscriptionService

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_assign_default_plan():
    Plan.objects.create(
        code="free", name="Бесплатный", price=Decimal("0"),
        is_default=True, is_active=True,
    )
    user = User.objects.create_user(
        email="billing@example.com", password="StrongPass!12345",
        display_name="Биллинг",
    )
    subscription = SubscriptionService.assign_default_plan(user)
    assert subscription.plan.code == "free"
    assert subscription.is_active()


def test_credit_topup_and_spend():
    user = User.objects.create_user(
        email="credit@example.com", password="StrongPass!12345",
        display_name="Кредиты",
    )
    CreditService.topup(user, Decimal("10.00"), reason="Пополнение")
    balance = CreditService.spend(user, Decimal("3.50"), reason="Списание")
    assert balance.balance == Decimal("6.5000")
    assert balance.lifetime_credited == Decimal("10.0000")
    assert balance.lifetime_spent == Decimal("3.5000")
