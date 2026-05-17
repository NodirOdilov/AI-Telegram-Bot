"""Единая URL-карта REST API.

Собирает ViewSet'ы из всех приложений в единый DefaultRouter,
а также подключает эндпоинты аутентификации (JWT).
"""
from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from apps.ai_engine.views import (
    AIModelViewSet,
    AIProviderViewSet,
    AIRequestLogViewSet,
    ImageGenerationView,
    PromptTemplateViewSet,
    TranscriptionView,
    TTSView,
)
from apps.analytics.views import (
    DailyUsageViewSet,
    SystemMetricViewSet,
    UsageEventViewSet,
)
from apps.billing.views import (
    CreditTransactionViewSet,
    InvoiceViewSet,
    PaymentViewSet,
    PlanViewSet,
    SubscriptionViewSet,
)
from apps.conversations.views import (
    AttachmentViewSet,
    ConversationViewSet,
    MessageViewSet,
)
from apps.notifications.views import (
    BroadcastViewSet,
    NotificationTemplateViewSet,
    NotificationViewSet,
)
from apps.plugins.views import (
    PluginConfigViewSet,
    PluginInvocationViewSet,
    PluginViewSet,
)
from apps.users.views import (
    APIKeyViewSet,
    AuditLogViewSet,
    CurrentUserView,
    LoginView,
    RegisterView,
    RoleViewSet,
    UserPreferenceView,
)

router = DefaultRouter()
router.register(r"plans", PlanViewSet, basename="plans")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscriptions")
router.register(r"invoices", InvoiceViewSet, basename="invoices")
router.register(r"payments", PaymentViewSet, basename="payments")
router.register(r"credits/transactions", CreditTransactionViewSet, basename="credit-transactions")

router.register(r"conversations", ConversationViewSet, basename="conversations")
router.register(r"messages", MessageViewSet, basename="messages")
router.register(r"attachments", AttachmentViewSet, basename="attachments")

router.register(r"ai/providers", AIProviderViewSet, basename="ai-providers")
router.register(r"ai/models", AIModelViewSet, basename="ai-models")
router.register(r"ai/templates", PromptTemplateViewSet, basename="ai-templates")
router.register(r"ai/logs", AIRequestLogViewSet, basename="ai-logs")
router.register(r"ai/images", ImageGenerationView, basename="ai-images")
router.register(r"ai/transcribe", TranscriptionView, basename="ai-transcribe")
router.register(r"ai/tts", TTSView, basename="ai-tts")

router.register(r"plugins", PluginViewSet, basename="plugins")
router.register(r"plugins/configs", PluginConfigViewSet, basename="plugin-configs")
router.register(r"plugins/invocations", PluginInvocationViewSet, basename="plugin-invocations")

router.register(r"analytics/events", UsageEventViewSet, basename="usage-events")
router.register(r"analytics/daily", DailyUsageViewSet, basename="daily-usage")
router.register(r"analytics/metrics", SystemMetricViewSet, basename="system-metrics")

router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"notifications/templates", NotificationTemplateViewSet, basename="notification-templates")
router.register(r"broadcasts", BroadcastViewSet, basename="broadcasts")

router.register(r"keys", APIKeyViewSet, basename="api-keys")
router.register(r"roles", RoleViewSet, basename="roles")
router.register(r"audit", AuditLogViewSet, basename="audit")

app_name = "api"

urlpatterns = [
    # Аутентификация
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token-verify"),

    # Профиль и настройки
    path("users/me/", CurrentUserView.as_view(), name="users-me"),
    path("users/me/preferences/", UserPreferenceView.as_view(), name="users-preferences"),

    # Все ViewSets через router
    path("", include(router.urls)),
]
