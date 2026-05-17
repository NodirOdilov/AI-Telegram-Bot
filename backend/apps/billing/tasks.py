"""Celery задачи биллинга."""
from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

from .models import Subscription
from .services import InvoiceService

logger = logging.getLogger(__name__)


@shared_task(name="apps.billing.tasks.renew_subscriptions")
def renew_subscriptions() -> int:
    """Перевыпускает счета для подписок с истёкшим периодом."""
    now = timezone.now()
    expiring = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE,
        autorenew=True,
        current_period_end__lte=now,
    )
    count = 0
    for sub in expiring:
        try:
            InvoiceService.create_for_subscription(sub)
            count += 1
        except Exception:
            logger.exception("Не удалось продлить подписку %s", sub.pk)
    return count


@shared_task(name="apps.billing.tasks.mark_expired_subscriptions")
def mark_expired_subscriptions() -> int:
    """Меняет статус истёкших подписок без автопродления."""
    now = timezone.now()
    expired = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE,
        autorenew=False,
        current_period_end__lt=now,
    )
    return expired.update(status=Subscription.Status.EXPIRED)
