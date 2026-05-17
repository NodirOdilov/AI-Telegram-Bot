"""Базовые smoke-тесты приложения users."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_create_email_user():
    user = User.objects.create_user(
        email="ivan@example.com", password="StrongPass!12345",
        display_name="Иван",
    )
    assert user.pk is not None
    assert user.check_password("StrongPass!12345")
    assert user.preferences is not None  # создаются через сигнал


def test_telegram_user_creation():
    user, created = User.objects.get_or_create_telegram_user(
        telegram_id=12345,
        username="vasiliy",
        first_name="Василий",
        last_name="Иванов",
        language_code="ru",
    )
    assert created
    assert user.telegram_profile.telegram_id == 12345

    user2, created2 = User.objects.get_or_create_telegram_user(telegram_id=12345)
    assert not created2
    assert user2.pk == user.pk
