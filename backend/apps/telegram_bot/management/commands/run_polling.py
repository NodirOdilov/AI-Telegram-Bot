"""Polling-режим для разработки (вместо webhook)."""
from __future__ import annotations

import logging
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.telegram_bot.services import UpdateRouter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Запускает Telegram-бота в режиме long polling."

    def handle(self, *args, **options) -> None:
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise CommandError("Не задан TELEGRAM_BOT_TOKEN.")

        offset = 0
        base = f"https://api.telegram.org/bot{token}"

        # На время polling вебхук должен быть отключён
        requests.post(f"{base}/deleteWebhook", json={"drop_pending_updates": False}, timeout=15)

        self.stdout.write(self.style.SUCCESS("Polling запущен. Ctrl+C для остановки."))
        while True:
            try:
                response = requests.get(
                    f"{base}/getUpdates",
                    params={"timeout": 30, "offset": offset},
                    timeout=60,
                ).json()
            except Exception:
                logger.exception("Ошибка получения обновлений")
                time.sleep(5)
                continue

            for update in response.get("result", []):
                offset = max(offset, update["update_id"] + 1)
                try:
                    UpdateRouter.handle(update)
                except Exception:
                    logger.exception("Ошибка обработки обновления")
