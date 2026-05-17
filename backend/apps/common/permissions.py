"""Переиспользуемые классы прав доступа."""
from __future__ import annotations

from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """Разрешает доступ владельцу объекта или администратору."""

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_staff:
            return True
        owner = getattr(obj, "owner", None) or getattr(obj, "user", None)
        return owner == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """Полный доступ — только администраторам, остальным — read-only."""

    def has_permission(self, request, view) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsAuthenticatedOrTelegram(permissions.BasePermission):
    """Разрешает доступ авторизованным или Telegram-пользователям."""

    def has_permission(self, request, view) -> bool:
        if request.user and request.user.is_authenticated:
            return True
        return bool(getattr(request, "telegram_user", None))
