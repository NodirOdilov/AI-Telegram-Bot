"""Management-команда регистрации встроенных плагинов в БД."""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.plugins.builtins import BUILTIN_PLUGINS
from apps.plugins.models import Plugin
from apps.plugins.registry import PluginRegistry


class Command(BaseCommand):
    help = "Регистрирует встроенные плагины в базе данных."

    def handle(self, *args, **options) -> None:
        created = 0
        updated = 0
        for plugin_cls, handler_path in BUILTIN_PLUGINS:
            obj, was_created = Plugin.objects.update_or_create(
                code=plugin_cls.code,
                defaults={
                    "name": plugin_cls.name,
                    "description": plugin_cls.description,
                    "handler_path": handler_path,
                    "schema": plugin_cls.schema,
                    "is_active": True,
                    "is_global": True,
                    "version": "1.0.0",
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
        PluginRegistry.invalidate()
        self.stdout.write(
            self.style.SUCCESS(
                f"Зарегистрировано плагинов: создано {created}, обновлено {updated}.",
            )
        )
