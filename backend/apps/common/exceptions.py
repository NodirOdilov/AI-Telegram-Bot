"""Унифицированная обработка исключений API.

Все ошибки приводятся к единому формату:
``{"error": {"code": ..., "message": ..., "details": {...}}}``.
"""
from __future__ import annotations

import logging
from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class DomainError(APIException):
    """Базовое доменное исключение."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Произошла ошибка обработки запроса."
    default_code = "domain_error"


class QuotaExceededError(DomainError):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Превышен лимит использования."
    default_code = "quota_exceeded"


class FeatureDisabledError(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Функция отключена администратором."
    default_code = "feature_disabled"


class IntegrationError(DomainError):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Ошибка внешней интеграции."
    default_code = "integration_error"


def standard_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Превращает любое исключение в стандартизированный JSON-ответ."""
    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Необработанное исключение API: %s", exc)
        return Response(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Внутренняя ошибка сервера.",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        code = getattr(exc, "default_code", "error")
        message = str(detail.pop("detail"))
        response.data = {
            "error": {
                "code": code,
                "message": message,
                "details": detail or {},
            }
        }
    else:
        response.data = {
            "error": {
                "code": getattr(exc, "default_code", "error"),
                "message": "Запрос отклонён.",
                "details": detail,
            }
        }
    return response
