"""View'ы AI движка."""
from __future__ import annotations

import base64

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import AIModel, AIProvider, AIRequestLog, PromptTemplate
from .serializers import (
    AIModelSerializer,
    AIProviderSerializer,
    AIRequestLogSerializer,
    PromptTemplateSerializer,
)
from .services import ImageService, TranscriptionService, TTSService


class AIProviderViewSet(viewsets.ModelViewSet):
    queryset = AIProvider.objects.all()
    serializer_class = AIProviderSerializer
    permission_classes = (permissions.IsAdminUser,)


class AIModelViewSet(viewsets.ModelViewSet):
    queryset = AIModel.objects.select_related("provider")
    serializer_class = AIModelSerializer
    permission_classes = (permissions.IsAdminUser,)

    def list(self, request, *args, **kwargs):
        # Список моделей доступен всем авторизованным пользователям
        self.permission_classes = (permissions.IsAuthenticated,)
        self.check_permissions(request)
        return super().list(request, *args, **kwargs)


class PromptTemplateViewSet(viewsets.ModelViewSet):
    queryset = PromptTemplate.objects.all()
    serializer_class = PromptTemplateSerializer
    permission_classes = (permissions.IsAuthenticated,)


class AIRequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIRequestLog.objects.order_by("-created_at")
    serializer_class = AIRequestLogSerializer
    permission_classes = (permissions.IsAdminUser,)


class ImageGenerationView(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request):
        prompt = request.data.get("prompt", "")
        if not prompt:
            return Response({"detail": "Промпт обязателен."}, status=400)
        response = ImageService().generate(request.user, prompt)
        return Response({
            "url": response.url,
            "revised_prompt": response.revised_prompt,
        })


class TranscriptionView(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, JSONParser)

    def create(self, request):
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return Response({"detail": "Аудиофайл обязателен."}, status=400)
        response = TranscriptionService().transcribe(
            request.user, audio_file.read(), filename=audio_file.name,
        )
        return Response({"text": response.text, "language": response.language})


class TTSView(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request):
        text = request.data.get("text", "")
        voice = request.data.get("voice", "alloy")
        if not text:
            return Response({"detail": "Текст обязателен."}, status=400)
        response = TTSService().synthesize(request.user, text, voice=voice)
        encoded = base64.b64encode(response.audio_bytes).decode("ascii")
        return Response(
            {"audio_base64": encoded, "mime_type": response.mime_type},
            status=status.HTTP_201_CREATED,
        )
