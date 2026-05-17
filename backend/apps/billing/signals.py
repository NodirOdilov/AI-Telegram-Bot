"""Сигналы биллинга."""
from __future__ import annotations

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CreditBalance
from .services import SubscriptionService


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def initialise_billing(sender, instance, created, **kwargs) -> None:
    """Создаёт балансы и подписку по умолчанию для нового пользователя."""
    if not created:
        return
    CreditBalance.objects.get_or_create(user=instance)
    try:
        SubscriptionService.assign_default_plan(instance)
    except Exception:
        # При отсутствии тарифов в системе подписка не создаётся
        pass
