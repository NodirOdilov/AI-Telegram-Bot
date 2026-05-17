"""Кастомные middleware проекта.

* ``RequestIDMiddleware`` — присваивает каждому запросу уникальный
  идентификатор, который добавляется в логи и заголовки ответа.
* ``AuditLogMiddleware`` — фиксирует ключевые действия пользователей
  в журнале аудита (вход/выход, изменения).
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("apps.common.requests")


class RequestIDMiddleware:
    """Прикрепляет уникальный ``X-Request-ID`` к каждому запросу."""

    HEADER_NAME = "HTTP_X_REQUEST_ID"
    RESPONSE_HEADER = "X-Request-ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.META.get(self.HEADER_NAME) or uuid.uuid4().hex
        request.request_id = request_id  # type: ignore[attr-defined]

        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000

        response[self.RESPONSE_HEADER] = request_id
        logger.info(
            "%s %s %s %.2fмс id=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


class AuditLogMiddleware(MiddlewareMixin):
    """Простейший аудит-логгер. Расширяется в приложении users."""

    def process_response(
        self, request: HttpRequest, response: HttpResponse,
    ) -> HttpResponse:
        # Для записи в журнал аудита достаточно знать пользователя и метод.
        # Подробная логика делегируется приложению users.
        return response
