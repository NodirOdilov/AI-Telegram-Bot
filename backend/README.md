# AI Telegram Bot Backend

Корпоративный Django-бэкенд для AI-Telegram бота. Реализует полный набор
модулей: пользователи, биллинг, диалоги, AI-движок, аналитика, плагины,
уведомления, REST API, WebSocket и интеграция с Telegram.

## Структура проекта

```
backend/
├── manage.py                 Точка входа управляющих команд
├── config/                   Конфигурация Django
│   ├── settings/             base / development / production / test
│   ├── celery.py             Celery приложение и расписание Beat
│   ├── urls.py               Корневой URL-конфигуратор
│   ├── wsgi.py / asgi.py     Точки входа production
├── apps/                     Бизнес-приложения
│   ├── common/               Базовые модели, middleware, exceptions
│   ├── users/                Пользователи, JWT, API-ключи, аудит
│   ├── billing/              Тарифы, подписки, счета, кредиты
│   ├── conversations/        Диалоги, сообщения, вложения
│   ├── ai_engine/            Провайдеры AI, чат/изображения/TTS/STT
│   ├── analytics/            События потребления, ежедневные агрегаты
│   ├── plugins/              Реестр плагинов, function calling
│   ├── notifications/        Уведомления, рассылки, шаблоны
│   ├── telegram_bot/         Webhook, polling, обработчики команд
│   └── api/                  Корневой роутер REST + WebSocket consumers
├── docker/                   Dockerfile, nginx.conf, entrypoint
├── docker-compose.yml        Локальная инфраструктура (Postgres, Redis, Celery, Daphne, Nginx)
├── requirements/             Зависимости (base/development/production)
├── Makefile                  Удобные команды
└── pyproject.toml            black/isort/ruff/mypy
```

## Технологии

- **Django 5** + **Django REST Framework** + **drf-spectacular** (OpenAPI)
- **PostgreSQL** + **Redis** + **Celery** + **Celery Beat** + **Flower**
- **Channels** + **Daphne** (WebSocket)
- **JWT** (simplejwt) + Telegram WebApp auth + API-ключи
- **OpenAI / Anthropic** SDK
- **Stripe** для платежей
- **Sentry**, **Prometheus**, **structlog** для наблюдаемости
- **django-axes**, **argon2**, **HSTS** для безопасности
- **Docker Compose** для развёртывания

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и заполните значения (как минимум
   `DJANGO_SECRET_KEY`, `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`).
2. Поднимите инфраструктуру:
   ```bash
   make up
   ```
3. Дождитесь готовности контейнеров и откройте:
   - Админ-панель — http://localhost/admin/
   - Swagger UI — http://localhost/api/docs/
   - Redoc — http://localhost/api/redoc/
   - Метрики — http://localhost/metrics
   - Flower — http://localhost:5555/

### Локальный запуск без Docker

```bash
python -m venv .venv && source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements/development.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py register_plugins
make run            # backend
make worker         # celery в другом терминале
make beat           # celery beat
make polling        # telegram-бот в режиме polling
```

## REST API

Все эндпоинты доступны под префиксом `/api/v1/`. Аутентификация — JWT
(`Authorization: Bearer ...`) или API-ключ (`Authorization: Token ...`)
или Telegram WebApp initData (`X-Telegram-Init-Data`).

Ключевые группы:

- `/auth/` — регистрация и JWT-токены.
- `/users/me/` — профиль и настройки.
- `/conversations/` — CRUD диалогов и `/chat` для генерации ответов.
- `/messages/`, `/attachments/` — сообщения и вложения.
- `/ai/*` — управление моделями, изображения, TTS, транскрипция.
- `/billing/*` — тарифы, подписки, счета, платежи.
- `/analytics/*` — события и агрегаты потребления.
- `/plugins/*` — плагины и их вызовы.
- `/notifications/*`, `/broadcasts/` — уведомления и рассылки.

## WebSocket

- `ws://host/ws/chat/<conversation_id>/` — стриминговый чат.
- `ws://host/ws/notifications/` — персональный канал уведомлений.

## Telegram

- **Webhook**: `POST /telegram/webhook/`. Установите URL командой
  `python manage.py setup_webhook`.
- **Polling** (для локальной разработки): `python manage.py run_polling`.
- Допустимые команды: `/start`, `/help`, `/reset`, `/image`, плюс
  любые текстовые/голосовые сообщения.

## Тесты, линтеры, форматирование

```bash
make test
make lint
make format
```

## Развёртывание

Docker-compose поднимает следующие сервисы:

| Сервис          | Назначение                                     |
|-----------------|------------------------------------------------|
| postgres        | Основная БД                                    |
| redis           | Кэш и брокер Celery / Channels                 |
| backend         | Django + Gunicorn (HTTP REST)                  |
| daphne          | Django Channels (WebSocket)                    |
| celery-worker   | Очередь асинхронных задач                      |
| celery-beat     | Расписание периодических задач                 |
| celery-flower   | Мониторинг очередей                            |
| telegram-bot    | Опрос Telegram (polling) или обработка webhook |
| nginx           | Reverse-proxy для HTTP и WebSocket             |

В production для масштабирования используйте отдельные кластеры Postgres
и Redis, заменяйте polling на webhook, поднимайте несколько worker'ов
Celery с очередями `default`, `telegram`, `ai`.
