"""Базовые модели и миксины, используемые во всём проекте.

Содержит:
* ``TimeStampedModel`` — добавляет поля created_at и updated_at.
* ``SoftDeletableModel`` — реализует мягкое удаление.
* ``UUIDModel`` — заменяет первичный ключ на UUID.
* ``OwnedModel`` — модель, привязанная к пользователю-владельцу.
* ``ActiveModel`` — модель с булевым флагом активности.
"""
from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Добавляет автоматические поля времени создания и обновления."""

    created_at = models.DateTimeField(
        _("создано"), auto_now_add=True, db_index=True,
    )
    updated_at = models.DateTimeField(
        _("обновлено"), auto_now=True,
    )

    class Meta:
        abstract = True


class SoftDeletableQuerySet(models.QuerySet):
    """QuerySet, скрывающий мягко удалённые записи."""

    def alive(self) -> "SoftDeletableQuerySet":
        return self.filter(deleted_at__isnull=True)

    def deleted(self) -> "SoftDeletableQuerySet":
        return self.filter(deleted_at__isnull=False)

    def delete(self) -> tuple[int, dict[str, int]]:  # type: ignore[override]
        # Помечаем записи удалёнными вместо физического удаления
        return self.update(deleted_at=timezone.now()), {}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()


class SoftDeletableManager(models.Manager.from_queryset(SoftDeletableQuerySet)):
    """Менеджер, по умолчанию возвращающий только живые записи."""

    def get_queryset(self) -> SoftDeletableQuerySet:
        return super().get_queryset().alive()


class SoftDeletableModel(models.Model):
    """Реализует мягкое удаление через поле ``deleted_at``."""

    deleted_at = models.DateTimeField(
        _("удалено"), null=True, blank=True, db_index=True,
    )

    objects = SoftDeletableManager()
    all_objects = SoftDeletableQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(
        self,
        using: str | None = None,
        keep_parents: bool = False,
        hard: bool = False,
    ) -> tuple[int, dict[str, int]]:
        """Мягко удаляет запись. Параметр ``hard=True`` запускает физическое удаление."""
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
        return 1, {self._meta.label: 1}

    def restore(self) -> None:
        """Восстанавливает мягко удалённую запись."""
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])


class UUIDModel(models.Model):
    """Модель с UUID в качестве первичного ключа."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        abstract = True


class OwnedModel(models.Model):
    """Модель, принадлежащая конкретному пользователю."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        verbose_name=_("владелец"),
        db_index=True,
    )

    class Meta:
        abstract = True


class ActiveModel(models.Model):
    """Модель с флагом активности."""

    is_active = models.BooleanField(_("активно"), default=True, db_index=True)

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel, UUIDModel):
    """Базовая модель с UUID и временными метками."""

    class Meta:
        abstract = True


def update_fields_diff(instance: models.Model, old_values: dict[str, Any]) -> list[str]:
    """Возвращает список изменённых полей по сравнению с ``old_values``."""
    changed: list[str] = []
    for field, previous in old_values.items():
        current = getattr(instance, field, None)
        if current != previous:
            changed.append(field)
    return changed
