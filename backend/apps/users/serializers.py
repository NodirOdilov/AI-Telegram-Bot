"""DRF сериализаторы приложения users."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import APIKey, AuditLog, Role, TelegramProfile, UserPreference

User = get_user_model()


class TelegramProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramProfile
        fields = (
            "telegram_id", "username", "first_name", "last_name",
            "language_code", "is_premium", "chat_id", "last_seen_at",
        )
        read_only_fields = fields


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        exclude = ("user",)


class UserSerializer(serializers.ModelSerializer):
    telegram = TelegramProfileSerializer(source="telegram_profile", read_only=True)
    preferences = UserPreferenceSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "display_name", "avatar", "bio",
            "language", "timezone", "account_type",
            "is_active", "is_staff", "is_verified",
            "two_factor_enabled",
            "telegram", "preferences",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "is_staff", "is_verified",
            "created_at", "updated_at", "account_type",
        )


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)
    display_name = serializers.CharField(max_length=128)
    language = serializers.CharField(max_length=8, default="ru")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class TokenPairSerializer(serializers.Serializer):
    """Возвращает пару access/refresh токенов вместе с профилем."""

    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)

    @classmethod
    def for_user(cls, user) -> dict:
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }


class APIKeySerializer(serializers.ModelSerializer):
    raw_key = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = APIKey
        fields = (
            "id", "name", "scopes", "key_prefix",
            "expires_at", "last_used_at", "revoked",
            "created_at", "raw_key",
        )
        read_only_fields = ("id", "key_prefix", "last_used_at", "created_at", "raw_key")


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "code", "name", "description", "permissions")


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.display_name", read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            "id", "actor", "actor_name", "action",
            "target_type", "target_id", "payload",
            "ip_address", "user_agent", "created_at",
        )
        read_only_fields = fields
