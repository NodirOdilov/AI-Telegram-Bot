"""View'ы плагинов."""
from __future__ import annotations

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Plugin, PluginConfig, PluginInvocation
from .registry import PluginRegistry
from .serializers import (
    PluginConfigSerializer,
    PluginInvocationSerializer,
    PluginSerializer,
)


class PluginViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plugin.objects.filter(is_active=True)
    serializer_class = PluginSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @action(detail=True, methods=["post"])
    def invoke(self, request, pk=None):
        plugin = self.get_object()
        arguments = request.data.get("arguments", {})
        result = PluginRegistry.invoke(plugin, arguments, user=request.user)
        return Response({
            "success": result.success,
            "data": result.data,
            "error": result.error,
        })


class PluginConfigViewSet(viewsets.ModelViewSet):
    serializer_class = PluginConfigSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return PluginConfig.objects.filter(user=self.request.user).select_related("plugin")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PluginInvocationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PluginInvocationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = PluginInvocation.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs
