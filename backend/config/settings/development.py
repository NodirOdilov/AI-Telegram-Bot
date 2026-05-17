"""Настройки для локальной разработки.

Включает Django Debug Toolbar, console email backend,
eager Celery (опционально) и менее строгие политики безопасности.
"""
from __future__ import annotations

from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, MIDDLEWARE, env

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Включаем Debug Toolbar и Silk для профилирования
INSTALLED_APPS += [
    "debug_toolbar",
    "silk",
]
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "silk.middleware.SilkyMiddleware",
]

INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Email — вывод в консоль
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Менее строгие политики безопасности — только для разработки
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Django Debug Toolbar выполняется только при включенном DEBUG
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

# CORS — разрешаем все источники в разработке
CORS_ALLOW_ALL_ORIGINS = True

# Eager Celery для упрощённой отладки (по желанию)
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = True
