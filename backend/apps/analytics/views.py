"""View'ы аналитики."""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DailyUsage, SystemMetric, UsageEvent
from .serializers import (
    DailyUsageSerializer,
    SystemMetricSerializer,
    UsageEventSerializer,
    UsageSummarySerializer,
)
from .services import UsageReport


class UsageEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UsageEventSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ("kind", "model")
    ordering = ("-created_at",)

    def get_queryset(self):
        qs = UsageEvent.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs

    @action(detail=False, methods=["get"])
    def summary(self, request):
        days = int(request.query_params.get("days", 30))
        since = (timezone.now() - timedelta(days=days)).date()
        data = UsageReport.summary(request.user, since=since)
        return Response(UsageSummarySerializer(data).data)


class DailyUsageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DailyUsageSerializer
    permission_classes = (permissions.IsAuthenticated,)
    ordering = ("-date",)

    def get_queryset(self):
        qs = DailyUsage.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs


class SystemMetricViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SystemMetricSerializer
    queryset = SystemMetric.objects.order_by("-timestamp")
    permission_classes = (permissions.IsAdminUser,)
