"""Команда установки/удаления Telegram webhook."""
from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.telegram_bot.services import TelegramSender


class Command(BaseCommand):
    help = "Устанавливает или удаляет webhook бота."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--delete", action="store_true",
            help="Удалить установленный webhook.",
        )
        parser.add_argument(
            "--url", default=settings.TELEGRAM_WEBHOOK_URL,
            help="URL webhook. По умолчанию берётся из TELEGRAM_WEBHOOK_URL.",
        )

    def handle(self, *args, **options) -> None:
        sender = TelegramSender()
        if options["delete"]:
            result = sender.delete_webhook()
            self.stdout.write(self.style.SUCCESS(f"Webhook удалён: {result}"))
            return

        url = options["url"]
        if not url:
            raise CommandError("Не задан URL webhook.")
        result = sender.set_webhook(url=url, secret_token=settings.TELEGRAM_WEBHOOK_SECRET)
        self.stdout.write(self.style.SUCCESS(f"Webhook установлен: {result}"))
