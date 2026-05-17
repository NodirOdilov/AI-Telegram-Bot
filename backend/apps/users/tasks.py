"""Celery задачи приложения users."""
from __future__ import annotations

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import APIKey

User = get_user_model()


@shared_task(name="apps.users.tasks.cleanup_expired_api_keys")
def cleanup_expired_api_keys() -> int:
    """Помечает просроченные API-ключи как отозванные."""
    now = timezone.now()
    qs = APIKey.objects.filter(revoked=False, expires_at__lt=now)
    count = qs.update(revoked=True)
    return count


@shared_task(name="apps.users.tasks.deactivate_inactive_users")
def deactivate_inactive_users(days: int = 180) -> int:
    """Деактивирует пользователей без активности дольше ``days`` дней."""
    threshold = timezone.now() - timezone.timedelta(days=days)
    qs = User.objects.filter(is_active=True, last_login__lt=threshold)
    return qs.update(is_active=False)
