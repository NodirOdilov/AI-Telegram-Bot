"""Celery задачи аналитики."""
from __future__ import annotations

import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import DailyUsage, SystemMetric

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(name="apps.analytics.tasks.reset_daily_usage")
def reset_daily_usage() -> int:
    """Создаёт пустые записи на новый день для активных пользователей."""
    today = timezone.now().date()
    created = 0
    for user in User.objects.filter(is_active=True).iterator():
        _, was_created = DailyUsage.objects.get_or_create(user=user, date=today)
        created += int(was_created)
    return created


@shared_task(name="apps.analytics.tasks.send_daily_reports")
def send_daily_reports() -> int:
    """Рассылает ежедневные отчёты администраторам."""
    from apps.notifications.services import NotificationService

    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    total_cost = (
        DailyUsage.objects.filter(date=yesterday)
        .values_list("cost", flat=True)
    )
    summary_cost = sum(total_cost, start=0)
    payload = {
        "date": yesterday.isoformat(),
        "total_cost": float(summary_cost),
        "users_active": len(list(total_cost)),
    }
    SystemMetric.objects.create(key="daily_total_cost", value=summary_cost, labels=payload)

    for admin in User.objects.filter(is_staff=True, is_active=True):
        NotificationService.send(
            user=admin,
            title="Ежедневный отчёт",
            body=f"За {yesterday}: ${summary_cost:.2f}, активных пользователей: {payload['users_active']}",
            payload=payload,
            channels=["telegram", "email"],
        )
    return len(list(total_cost))
