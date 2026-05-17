"""View'ы биллинга."""
from __future__ import annotations

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CreditTransaction, Invoice, Payment, Plan, Subscription
from .serializers import (
    CreditTransactionSerializer,
    InvoiceSerializer,
    PaymentSerializer,
    PlanSerializer,
    SubscriptionSerializer,
)
from .services import InvoiceService, SubscriptionService


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """Доступные тарифы."""

    serializer_class = PlanSerializer
    queryset = Plan.objects.filter(is_active=True)
    permission_classes = (permissions.AllowAny,)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ("get", "post", "delete")

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related("plan")

    def perform_create(self, serializer):
        sub = serializer.save(user=self.request.user)
        InvoiceService.create_for_subscription(sub)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        sub = self.get_object()
        SubscriptionService.cancel(sub, immediate=request.data.get("immediate", False))
        return Response({"status": "cancelled"})


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Payment.objects.filter(invoice__user=self.request.user)


class CreditTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CreditTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return CreditTransaction.objects.filter(user=self.request.user)
