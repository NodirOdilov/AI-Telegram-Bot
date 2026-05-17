"""Celery задачи уведомлений."""
from __future__ import annotations

import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from .models import Broadcast
from .services import NotificationService

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(name="apps.notifications.tasks.send_notification")
def send_notification(user_id: str, title: str, body: str, channels: list[str]) -> bool:
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return False
    NotificationService.send(user, title=title, body=body, channels=channels)
    return True


@shared_task(name="apps.notifications.tasks.run_broadcast")
def run_broadcast(broadcast_id: str) -> int:
    try:
        broadcast = Broadcast.objects.get(pk=broadcast_id)
    except Broadcast.DoesNotExist:
        return 0

    broadcast.status = Broadcast.Status.RUNNING
    broadcast.save(update_fields=["status"])

    qs = User.objects.filter(is_active=True)
    audience = broadcast.audience_filter or {}
    if filter_lang := audience.get("language"):
        qs = qs.filter(language=filter_lang)
    if filter_plan := audience.get("plan_code"):
        qs = qs.filter(subscriptions__plan__code=filter_plan).distinct()

    sent = 0
    failed = 0
    for user in qs.iterator():
        try:
            NotificationService.send(
                user=user,
                title=broadcast.title,
                body=broadcast.body,
                channels=broadcast.channels or ["websocket"],
            )
            sent += 1
        except Exception:
            logger.exception("Ошибка отправки рассылки %s пользователю %s",
                             broadcast.pk, user.pk)
            failed += 1

    broadcast.sent_count = sent
    broadcast.failed_count = failed
    broadcast.status = Broadcast.Status.COMPLETED
    broadcast.save(update_fields=["sent_count", "failed_count", "status"])
    return sent
