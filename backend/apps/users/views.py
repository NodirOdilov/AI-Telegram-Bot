"""View'ы приложения users."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.permissions import IsOwnerOrAdmin

from .models import APIKey, AuditLog, Role, UserPreference
from .serializers import (
    APIKeySerializer,
    AuditLogSerializer,
    RegistrationSerializer,
    RoleSerializer,
    TokenPairSerializer,
    UserPreferenceSerializer,
    UserSerializer,
)
from .services import APIKeyService

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя."""

    permission_classes = (permissions.AllowAny,)
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = TokenPairSerializer.for_user(user)
        return Response(tokens, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """Получение пары JWT-токенов."""

    serializer_class = None  # используется стандартный сериализатор simple_jwt

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data.get("email"))
            response.data["user"] = UserSerializer(user).data
        return response


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """Получение и обновление профиля текущего пользователя."""

    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UserPreferenceView(generics.RetrieveUpdateAPIView):
    """Настройки текущего пользователя."""

    serializer_class = UserPreferenceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        preference, _ = UserPreference.objects.get_or_create(user=self.request.user)
        return preference


class APIKeyViewSet(viewsets.ModelViewSet):
    """CRUD управление API-ключами пользователя."""

    serializer_class = APIKeySerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrAdmin)
    http_method_names = ("get", "post", "delete")

    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        name = request.data.get("name") or "default"
        scopes = request.data.get("scopes") or []
        issued = APIKeyService.issue(request.user, name=name, scopes=scopes)
        serializer = self.get_serializer(issued.api_key)
        data = serializer.data
        data["raw_key"] = issued.raw_key  # показываем один раз
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        api_key = self.get_object()
        APIKeyService.revoke(api_key, actor=request.user)
        return Response({"status": "revoked"}, status=status.HTTP_200_OK)


class RoleViewSet(viewsets.ModelViewSet):
    """Управление ролями (только для администраторов)."""

    serializer_class = RoleSerializer
    permission_classes = (permissions.IsAdminUser,)
    queryset = Role.objects.all().order_by("code")


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр журнала аудита (только для администраторов)."""

    serializer_class = AuditLogSerializer
    permission_classes = (permissions.IsAdminUser,)
    queryset = AuditLog.objects.select_related("actor").order_by("-created_at")
    filterset_fields = ("action", "actor", "target_type")
    search_fields = ("target_id", "target_type")
