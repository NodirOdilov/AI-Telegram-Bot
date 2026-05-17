"""Сигналы приложения users."""
from __future__ import annotations

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserPreference


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_preferences(sender, instance, created, **kwargs) -> None:
    """Автоматически создаёт настройки пользователя при регистрации."""
    if created:
        UserPreference.objects.get_or_create(user=instance)
