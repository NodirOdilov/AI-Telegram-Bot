"""Настройки production окружения.

Включает строгие политики безопасности, Sentry, оптимизации
для нагрузки, отключение DEBUG и принудительный HTTPS.
"""
from __future__ import annotations

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F401,F403
from .base import SENTRY_DSN, env

DEBUG = False

# Строгие политики безопасности
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "same-origin"

# Allowed hosts должен быть строго задан
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# Email через SMTP/Anymail
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="anymail.backends.mailgun.EmailBackend",
)

# Sentry
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=env.float("SENTRY_TRACES_RATE", default=0.1),
        profiles_sample_rate=env.float("SENTRY_PROFILES_RATE", default=0.1),
        send_default_pii=False,
        environment=env("SENTRY_ENVIRONMENT", default="production"),
    )

# Логирование в JSON-формате для систем агрегации (ELK, Loki)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "json_console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {"handlers": ["json_console"], "level": "INFO"},
}
