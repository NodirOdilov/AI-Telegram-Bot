"""Webhook-эндпоинты Telegram."""
from __future__ import annotations

import json
import logging

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services import UpdateRouter
from .tasks import process_telegram_update

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def telegram_webhook(request: HttpRequest) -> JsonResponse:
    """Принимает обновления от Telegram и ставит их в очередь."""
    secret_header = request.META.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN", "")
    expected_secret = settings.TELEGRAM_WEBHOOK_SECRET
    if expected_secret and secret_header != expected_secret:
        return JsonResponse({"detail": "Invalid secret"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid payload"}, status=400)

    # Асинхронная обработка, синхронный fallback при отсутствии брокера
    try:
        process_telegram_update.delay(payload)
    except Exception:
        logger.exception("Не удалось поставить задачу в очередь, обрабатываем синхронно.")
        UpdateRouter.handle(payload)

    return JsonResponse({"ok": True})
