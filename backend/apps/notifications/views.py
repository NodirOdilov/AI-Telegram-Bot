"""View'ы уведомлений."""
from __future__ import annotations

from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Broadcast, Notification, NotificationTemplate
from .serializers import (
    BroadcastSerializer,
    NotificationSerializer,
    NotificationTemplateSerializer,
)
from .tasks import run_broadcast


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.status = Notification.Status.READ
        notification.read_at = timezone.now()
        notification.save(update_fields=["status", "read_at"])
        return Response({"status": "read"})


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = (permissions.IsAdminUser,)


class BroadcastViewSet(viewsets.ModelViewSet):
    queryset = Broadcast.objects.all()
    serializer_class = BroadcastSerializer
    permission_classes = (permissions.IsAdminUser,)

    @action(detail=True, methods=["post"])
    def launch(self, request, pk=None):
        broadcast = self.get_object()
        run_broadcast.delay(str(broadcast.id))
        return Response({"status": "queued"})
