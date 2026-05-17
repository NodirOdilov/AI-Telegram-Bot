"""Конфигурация админ-панели для пользовательских моделей."""
from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    APIKey,
    AuditLog,
    Role,
    TelegramProfile,
    User,
    UserPreference,
    UserRole,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "display_name", "email", "account_type",
        "is_active", "is_staff", "is_verified", "created_at",
    )
    list_filter = ("account_type", "is_active", "is_staff", "is_verified")
    search_fields = ("email", "display_name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "last_login", "last_login_ip")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профиль", {"fields": ("display_name", "avatar", "bio", "language", "timezone")}),
        ("Тип аккаунта", {"fields": ("account_type", "is_verified", "two_factor_enabled")}),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Метаданные", {"fields": ("last_login", "last_login_ip", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "display_name", "password1", "password2"),
        }),
    )


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "user", "is_premium", "last_seen_at")
    search_fields = ("telegram_id", "username", "first_name", "last_name")
    list_filter = ("is_premium", "is_blocked", "language_code")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "granted_by", "expires_at")
    autocomplete_fields = ("user", "role", "granted_by")


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "preferred_model", "temperature", "stream_responses")
    search_fields = ("user__email", "user__display_name")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "target_type", "target_id")
    list_filter = ("action", "target_type")
    search_fields = ("actor__email", "target_id")
    readonly_fields = (
        "actor", "action", "target_type", "target_id",
        "payload", "ip_address", "user_agent", "created_at",
    )

    def has_add_permission(self, request) -> bool:
        return False


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "key_prefix", "revoked", "expires_at", "last_used_at")
    list_filter = ("revoked",)
    search_fields = ("name", "key_prefix", "user__email")
    readonly_fields = ("key_prefix", "key_hash", "last_used_at", "created_at")
