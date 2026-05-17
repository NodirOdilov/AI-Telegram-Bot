"""Celery приложение проекта.

Подхватывает настройки из Django (CELERY_*), автоматически обнаруживает
задачи во всех зарегистрированных приложениях и регистрирует расписание
Celery Beat по умолчанию.
"""
from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("aibot")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# Расписание периодических задач по умолчанию.
# При наличии django-celery-beat реальное расписание хранится в БД и
# может быть изменено через админ-панель — это значения по умолчанию.
app.conf.beat_schedule = {
    "reset-daily-usage": {
        "task": "apps.analytics.tasks.reset_daily_usage",
        "schedule": crontab(hour=0, minute=5),
    },
    "renew-subscriptions": {
        "task": "apps.billing.tasks.renew_subscriptions",
        "schedule": crontab(hour="*/1", minute=15),
    },
    "cleanup-old-conversations": {
        "task": "apps.conversations.tasks.cleanup_old_conversations",
        "schedule": crontab(hour=3, minute=30),
    },
    "send-daily-reports": {
        "task": "apps.analytics.tasks.send_daily_reports",
        "schedule": crontab(hour=8, minute=0),
    },
    "refresh-plugin-cache": {
        "task": "apps.plugins.tasks.refresh_plugin_cache",
        "schedule": crontab(minute="*/30"),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:
    """Диагностическая задача для проверки работоспособности Celery."""
    print(f"Запрос: {self.request!r}")
