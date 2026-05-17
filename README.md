<div align="center">

# NeuroLink

**Корпоративная AI-платформа на базе Telegram — мультимодельный ассистент, биллинг, плагины, аналитика и WebSocket в одном решении под вашим контролем.**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django 5](https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-A30000?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Channels](https://img.shields.io/badge/Channels-4.x-44B78B?style=for-the-badge&logo=django&logoColor=white)](https://channels.readthedocs.io/)
[![Celery 5](https://img.shields.io/badge/Celery-5-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis 7](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Nginx](https://img.shields.io/badge/Nginx-Reverse%20Proxy-009639?style=for-the-badge&logo=nginx&logoColor=white)](https://nginx.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?style=for-the-badge&logo=openai&logoColor=white)](https://platform.openai.com/)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude-191919?style=for-the-badge)](https://www.anthropic.com/)
[![JWT](https://img.shields.io/badge/Auth-JWT%20%2B%20API%20Key-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Stripe](https://img.shields.io/badge/Stripe-Payments-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://stripe.com/)
[![Sentry](https://img.shields.io/badge/Sentry-Monitoring-362D59?style=for-the-badge&logo=sentry&logoColor=white)](https://sentry.io/)
[![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)
[![License GPL 2.0](https://img.shields.io/badge/License-GPL%202.0-A42E2B?style=for-the-badge&logo=gnu&logoColor=white)](LICENSE)

</div>

---

## Содержание

1. [О проекте](#1-о-проекте)
2. [Ключевые возможности](#2-ключевые-возможности)
3. [Технологический стек](#3-технологический-стек)
4. [Структура репозитория](#4-структура-репозитория)
5. [Архитектура и как это работает](#5-архитектура-и-как-это-работает)
6. [Доменная модель (крупными блоками)](#6-доменная-модель-крупными-блоками)
7. [Сервисы в Docker Compose](#7-сервисы-в-docker-compose)
8. [Быстрый старт (локально, Docker)](#8-быстрый-старт-локально-docker)
9. [Основные команды Makefile](#9-основные-команды-makefile)
10. [Ручной запуск backend и Telegram-бота](#10-ручной-запуск-backend-и-telegram-бота)
11. [Конфигурация и переменные окружения](#11-конфигурация-и-переменные-окружения)
12. [API, очереди и интеграции](#12-api-очереди-и-интеграции)
13. [Мониторинг и эксплуатация](#13-мониторинг-и-эксплуатация)
14. [CI/CD](#14-cicd)
15. [Безопасность и хранение данных](#15-безопасность-и-хранение-данных)
16. [Роли компонентов в продакшене](#16-роли-компонентов-в-продакшене)
17. [Лицензия](#17-лицензия)
18. [Поддержка](#18-поддержка)

---

## 1. О проекте

**NeuroLink** — это **корпоративная SaaS-платформа AI-ассистентов**, использующая Telegram как
основной канал общения с пользователем и предоставляющая полноценный REST/WebSocket API
для веб-интерфейсов, мобильных клиентов и внешних интеграторов. Система объединяет в одном
продукте: интеллектуальный чат на базе моделей OpenAI/Anthropic, генерацию изображений,
синтез и распознавание речи, биллинг с подписками и кредитами, плагинную систему с function
calling, многоканальные уведомления, аналитику потребления и журнал аудита.

### Что это за тип системы

По архитектуре NeuroLink — **многосервисная распределённая платформа** (не монолит «в одном
процессе»):

| Аспект         | Описание                                                                                     |
|----------------|----------------------------------------------------------------------------------------------|
| Продукт        | B2C/B2B-сервис AI-ассистентов с подписками, кредитами, квотами, аудитом и SLA                |
| Архитектура    | Django API + Channels (ASGI) + Celery воркеры + Telegram бот + Nginx reverse-proxy           |
| Хранилище      | PostgreSQL (метаданные) + Redis (кэш, очереди, channel layer) + S3/MinIO (медиа, опционально) |
| Каналы доступа | Telegram (webhook/polling), REST API, WebSocket, Admin Panel, OpenAPI/Swagger                |
| Безопасность   | JWT, API-ключи, Telegram WebApp HMAC, RBAC, audit log, Argon2, django-axes, HSTS             |
| Биллинг        | Подписки, тарифы, квоты на токены/изображения/TTS/STT, кредитный кошелёк, инвойсы, Stripe    |
| Расширяемость  | Реестр плагинов с JSON-схемами для function calling, провайдеры AI как заменяемые адаптеры   |

### Для кого

- **Стартапы и команды**, которым нужен готовый каркас AI-продукта с биллингом и аналитикой.
- **Корпоративные клиенты**, разворачивающие AI-ассистента в своём контуре с собственными
  ключами и аудитом.
- **Интеграторы**, желающие подключить AI-бот к существующим CRM, ITSM, BPM-системам через
  REST/WebSocket.

---

## 2. Ключевые возможности

### Чат и диалоги
- Многошаговые диалоги с памятью, автоматической сводкой контекста и поддержкой нескольких
  моделей в одном пользователе.
- Стриминг ответов AI через WebSocket (Channels) и HTTP SSE.
- Прикрепление изображений, голосовых сообщений, документов; распознавание голоса (Whisper)
  и ответ синтезированной речью (TTS).
- Сброс диалога, архивирование, закрепление, поиск по сообщениям, фильтрация по источникам.

### Мультимодельный AI-движок
- Унифицированные адаптеры провайдеров: **OpenAI**, **Anthropic Claude**, расширяется одним
  классом-наследником `BaseProvider`.
- Каталог моделей (`AIModel`) с прайсингом за input/output токены, изображения и аудио —
  стоимость считается автоматически по каждому запросу.
- Шаблоны промптов (`PromptTemplate`) с переменными и журнал всех вызовов провайдеров
  (`AIRequestLog`) для отладки и аудита.

### Биллинг и квоты
- Тарифные планы с произвольным набором лимитов (токены, изображения, секунды
  транскрипции, символы TTS, vision-запросы) и пакетом включённых функций.
- Подписки с пробным периодом, автопродлением, паузой, отменой и отдельным жизненным
  циклом инвойсов.
- Внутренние **кредиты** с топ-ап/списанием/бонусами и полным журналом транзакций.
- Платежи через **Stripe** и Telegram Payments, ручное подтверждение через админ-панель.
- Сервис `QuotaService` единообразно проверяет лимит до выполнения операции и бросает
  `QuotaExceededError`, что корректно превращается в `HTTP 402 Payment Required`.

### Плагинная система
- Реестр плагинов с кэшированием, конфигурацией на уровне пользователя и журналом вызовов.
- Готовые встроенные плагины: погода (Open-Meteo), время, веб-поиск (DuckDuckGo).
- Автоматическая выдача OpenAI-совместимых JSON-схем для function calling.

### Telegram-интеграция
- Поддержка **webhook** (production) и **polling** (разработка) одинаковым кодом.
- Идемпотентная обработка обновлений с журналом `TelegramUpdate`, повторы Celery, HMAC-проверка
  WebApp `initData`.
- Команды бота через декораторный `CommandHandlerRegistry`: `/start`, `/help`, `/reset`,
  `/image` и любые пользовательские.

### REST и WebSocket API
- 30+ ViewSet'ов, единая JWT/API-Key/Telegram-аутентификация, стандартизированная пагинация,
  фильтры, поиск, сортировка.
- Автогенерация **OpenAPI 3.1** через drf-spectacular, Swagger UI и Redoc «из коробки».
- WebSocket-консьюмеры: персональный канал уведомлений и стриминговый чат.

### Уведомления и рассылки
- Универсальный `NotificationService` с тремя каналами: **email**, **Telegram**, **WebSocket**.
- Сущность `Broadcast` для массовых рассылок с фильтрами аудитории (язык, тариф, активность).

### Аналитика и аудит
- Сырые события `UsageEvent`, ежедневные агрегаты `DailyUsage`, произвольные `SystemMetric`.
- Журнал аудита `AuditLog` со ссылкой на актора, цель, IP и user-agent.
- Готовый эндпоинт `GET /analytics/events/summary?days=30`.

### Безопасность
- Argon2 для паролей, JWT с ротацией refresh-токенов, blacklist, django-axes (защита от
  bruteforce), 2FA-готовность, HSTS, CSP-headers через nginx.
- Telegram WebApp `initData` валидируется HMAC-SHA256 с проверкой `auth_date`.

---

## 3. Технологический стек

### Backend
| Категория        | Технологии                                                              |
|------------------|-------------------------------------------------------------------------|
| Язык             | Python 3.12                                                             |
| Web-фреймворк    | Django 5.0, Django REST Framework 3.15                                  |
| ASGI / WS        | Channels 4, Daphne 4, channels-redis                                    |
| Очереди          | Celery 5, Celery Beat, Flower, Redis broker                             |
| База данных      | PostgreSQL 16 (`psycopg[binary,pool]`), django-prometheus DB backend    |
| Кэш / Channels   | Redis 7, hiredis, django-redis                                          |
| Документация API | drf-spectacular, Swagger UI, Redoc                                      |
| Безопасность     | simplejwt, django-axes, argon2-cffi, pyotp, cryptography                |
| Платежи          | Stripe SDK                                                              |
| AI               | OpenAI SDK, Anthropic SDK, Google Generative AI, tiktoken               |
| Аудио            | pydub, gTTS, SpeechRecognition, mutagen, ffmpeg                         |
| Интеграции       | DuckDuckGo Search, Wolfram Alpha, Spotipy, Pytube, yfinance             |
| Мониторинг       | Sentry, django-prometheus, structlog, python-json-logger, django-silk   |
| Тесты            | pytest, pytest-django, pytest-asyncio, factory-boy, freezegun           |
| Линтеры          | ruff, black, isort, flake8, mypy + django-stubs, bandit                 |

### Infrastructure
| Категория        | Технологии                                                              |
|------------------|-------------------------------------------------------------------------|
| Контейнеризация  | Docker, Docker Compose                                                  |
| Reverse-proxy    | Nginx 1.27 (HTTP + WebSocket upstream)                                  |
| HTTP-сервер      | Gunicorn (WSGI) для REST                                                |
| ASGI-сервер      | Daphne для Channels/WebSocket                                           |
| Хранилище медиа  | Локально (`media_data` volume) или S3/MinIO через django-storages       |
| Очереди задач    | Redis-backed Celery, отдельные очереди `default`, `telegram`, `ai`      |
| Метрики          | `/metrics` Prometheus endpoint, Flower UI, healthcheck endpoint         |

---

## 4. Структура репозитория

```
AI-Telegram-Bot/
├── backend/                          # Django-бэкенд (основное приложение)
│   ├── manage.py                     # Точка входа управляющих команд
│   ├── conftest.py                   # Глобальные фикстуры pytest
│   ├── pytest.ini  pyproject.toml    # Конфигурация тестов и линтеров
│   ├── Makefile                      # Команды разработки и деплоя
│   ├── docker-compose.yml            # Полный набор сервисов
│   ├── .env.example                  # Шаблон переменных окружения
│   ├── README.md                     # Документация бэкенда
│   ├── requirements/                 # base.txt / development.txt / production.txt
│   ├── docker/                       # Dockerfile, nginx.conf, entrypoint.sh
│   │   ├── django/Dockerfile         # Многоэтапный образ для backend/celery/daphne
│   │   ├── nginx/nginx.conf          # Reverse-proxy HTTP + WebSocket
│   │   └── entrypoint.sh             # Миграции, статика, плагины, запуск
│   ├── config/                       # Конфигурация проекта
│   │   ├── settings/                 # base, development, production, test
│   │   ├── urls.py                   # Корневой URL-конфигуратор
│   │   ├── celery.py                 # Celery приложение и Beat-расписание
│   │   ├── wsgi.py / asgi.py         # WSGI и ASGI точки входа
│   └── apps/                         # Бизнес-приложения
│       ├── common/                   # BaseModel, middleware, pagination, exceptions
│       ├── users/                    # User, TelegramProfile, RBAC, APIKey, JWT, аудит
│       ├── billing/                  # Plan, Subscription, Invoice, Payment, кредиты
│       ├── conversations/            # Диалоги, сообщения, вложения, контекст
│       ├── ai_engine/                # Провайдеры AI, чат/изображения/TTS/STT, прайсинг
│       ├── analytics/                # UsageEvent, DailyUsage, отчёты, метрики
│       ├── plugins/                  # Plugin, PluginConfig, registry, function calling
│       ├── notifications/            # Notification, Broadcast, email/Telegram/WS каналы
│       ├── telegram_bot/             # Webhook, polling, command handlers
│       └── api/                      # Корневой DRF router + Channels routing/consumers
├── bot/                              # Устаревший standalone-бот (сохранён для совместимости)
├── translations.json                 # Старые локализации (мигрируются в Django i18n)
├── README.md                         # Этот файл
├── LICENSE                           # GPL-2.0
└── .gitignore
```

---

## 5. Архитектура и как это работает

```
                              ┌──────────────────────────────┐
                              │   Telegram Bot API (Cloud)   │
                              └───────────────┬──────────────┘
                                              │ webhook / polling
                                              ▼
┌────────────────┐    HTTPS    ┌──────────────────────────────┐    AMQP/Redis    ┌──────────────────┐
│  React / Web   │ ──────────▶ │           Nginx              │ ───────────────▶ │ Celery Workers   │
│  Mobile / TG   │ ◀────────── │  reverse-proxy + WS upstream │ ◀─────────────── │ (default,        │
│  WebApp        │             └───────┬──────────────────────┘                  │  telegram, ai)   │
└────────────────┘                     │                                         └──────┬───────────┘
                                       │                                                │
                              ┌────────┴────────┐                                       │
                              ▼                 ▼                                       │
                     ┌────────────────┐ ┌────────────────┐                              │
                     │ Gunicorn (WSGI)│ │ Daphne  (ASGI) │                              │
                     │  Django REST   │ │  Channels WS   │                              │
                     │  Admin / Auth  │ │  Chat / Notify │                              │
                     └───────┬────────┘ └────────┬───────┘                              │
                             │                   │                                      │
                             └─────────┬─────────┘                                      │
                                       ▼                                                │
                              ┌────────────────────┐         ┌──────────────────┐       │
                              │ PostgreSQL 16      │ ◀────── │ Celery Beat      │       │
                              │ + django-prom      │         │ (cron-расписание)│       │
                              └────────┬───────────┘         └──────────────────┘       │
                                       │                                                │
                              ┌────────┴───────────┐                                    │
                              │ Redis 7            │ ◀──────────────────────────────────┘
                              │ cache + broker +   │
                              │ channel layer      │
                              └────────────────────┘
```

**Поток типового запроса от Telegram:**

1. Telegram отправляет `POST /telegram/webhook/` с HMAC-secret в заголовке.
2. Nginx проксирует запрос на `backend` (Gunicorn).
3. View валидирует секрет, сохраняет `TelegramUpdate` в БД и ставит задачу
   `process_telegram_update.delay(payload)` в Celery.
4. Worker (`celery-worker`) поднимает `UpdateRouter`, находит или создаёт пользователя по
   `telegram_id`, расшифровывает голос (если нужно) через Whisper, маршрутизирует команду или
   диалог.
5. `ChatService` проверяет квоту через `QuotaService`, собирает историю,
   вызывает соответствующий `Provider`, считает стоимость через `CostCalculator`,
   сохраняет сообщение и фиксирует `UsageEvent`/`DailyUsage`.
6. `TelegramSender` отправляет ответ в чат, а `NotificationService` через WebSocket
   уведомляет открытые веб-сессии пользователя.

**Поток REST-запроса от веб-клиента** аналогичен, но проходит напрямую через DRF без
очереди — синхронно, со стримингом ответа по SSE/WebSocket.

---

## 6. Доменная модель (крупными блоками)

### Пользователи и доступ (`apps/users`)
- **User** — UUID, email/telegram, аватар, язык, таймзона, 2FA-поля.
- **TelegramProfile** — связь с Telegram, `telegram_id`, `chat_id`, `username`, премиум-флаг.
- **Role / UserRole** — расширенный RBAC поверх стандартных групп Django.
- **UserPreference** — модель по умолчанию, температура, max_tokens, voice_only, кастомный
  промпт, набор включённых функций.
- **APIKey** — выпуск/отзыв программных ключей с префиксом, скоупами и сроком действия.
- **AuditLog** — единый журнал действий: login, create, update, delete, payment, system.

### Биллинг (`apps/billing`)
- **Plan** — тариф (цена, период, квоты по 5 ресурсам, JSON features, default-флаг).
- **Subscription** — статусы `trial/active/paused/cancelled/expired`, периоды, autorenew.
- **Invoice** — счёт с номером `INV-YYYYMM-XXXX`, line items, статусы и due date.
- **Payment** — провайдеры: Stripe, Telegram, Manual, Internal.
- **CreditBalance / CreditTransaction** — внутренний кошелёк с историей пополнений/списаний.

### Диалоги (`apps/conversations`)
- **Conversation** — UUID, источник (telegram/web/api), модель, system_prompt, soft-delete.
- **Message** — роль, статус (pending/streaming/completed/failed), токены, стоимость,
  tool_name/arguments/response, reply_to.
- **Attachment** — image/audio/video/document/voice/sticker с MIME и метаданными.
- **ConversationContext** — сжатая сводка для экономии токенов.

### AI-движок (`apps/ai_engine`)
- **AIProvider** — openai, anthropic, google, локальные.
- **AIModel** — модальность (chat/image/audio/vision/embedding/tts), контекстное окно,
  прайсинг, флаги `supports_functions/vision/streaming`.
- **PromptTemplate** — шаблоны с переменными и локалью.
- **AIRequestLog** — запрос/ответ/ошибка/латентность каждого вызова провайдера.

### Аналитика (`apps/analytics`)
- **UsageEvent** — сырое событие потребления (chat/image/vision/transcription/tts/tool).
- **DailyUsage** — ежедневный агрегат по 5 ресурсам и стоимости.
- **SystemMetric** — произвольная численная метрика с лейблами.

### Плагины (`apps/plugins`)
- **Plugin** — описание, версия, JSON-схема, путь обработчика.
- **PluginConfig** — настройки плагина для конкретного пользователя.
- **PluginInvocation** — журнал вызовов с длительностью, аргументами и результатом.

### Уведомления (`apps/notifications`)
- **NotificationTemplate** — шаблоны subject/body/html с переменными.
- **Notification** — конкретное уведомление, список каналов, статус (sent/failed/read).
- **Broadcast** — массовая рассылка с фильтром аудитории и счётчиками.

### Telegram (`apps/telegram_bot`)
- **TelegramUpdate** — журнал входящих обновлений (идемпотентность).
- **TelegramCommand** — реестр команд бота для отображения в меню.

---

## 7. Сервисы в Docker Compose

| Сервис           | Образ / команда                                  | Назначение                                          | Порт |
|------------------|--------------------------------------------------|-----------------------------------------------------|------|
| `postgres`       | `postgres:16-alpine`                             | Основная БД                                         | 5432 |
| `redis`          | `redis:7-alpine`                                 | Кэш + брокер Celery + channel layer                 | 6379 |
| `backend`        | `gunicorn config.wsgi`                           | REST API, Admin, OpenAPI                            | 8000 |
| `daphne`         | `daphne config.asgi`                             | WebSocket (Channels)                                | 8001 |
| `celery-worker`  | `celery -A config worker -Q default,telegram,ai` | Асинхронные задачи (AI, рассылки, Telegram)         |  —   |
| `celery-beat`    | `celery -A config beat`                          | Cron-расписание                                     |  —   |
| `celery-flower`  | `celery -A config flower --port 5555`            | Мониторинг очередей                                 | 5555 |
| `telegram-bot`   | `python manage.py run_polling`                   | Long-polling Telegram (альтернатива webhook)        |  —   |
| `nginx`          | `nginx:1.27-alpine`                              | Reverse-proxy HTTP + WebSocket, отдача static/media |  80  |

Все сервисы используют общий [`.env`](backend/.env.example), общую сеть compose и тома
`postgres_data`, `redis_data`, `media_data`, `static_data`.

---

## 8. Быстрый старт (локально, Docker)

### Предварительные требования
- Docker Desktop 4.30+ или Docker Engine 25+ с Compose v2
- Свободные порты: 80, 5432, 6379, 8000, 8001, 5555
- 4 ГБ свободной RAM

### Шаги

```bash
# 1. Клонируем репозиторий
git clone https://github.com/NodirOdilov/AI-Telegram-Bot.git
cd AI-Telegram-Bot/backend

# 2. Готовим переменные окружения
cp .env.example .env
# отредактируйте .env: DJANGO_SECRET_KEY, OPENAI_API_KEY, TELEGRAM_BOT_TOKEN

# 3. Поднимаем всю инфраструктуру
make up               # эквивалент `docker compose up -d --build`

# 4. Создаём суперпользователя (одноразово)
docker compose exec backend python manage.py createsuperuser

# 5. Регистрируем встроенные плагины
docker compose exec backend python manage.py register_plugins

# 6. Опционально: устанавливаем webhook Telegram (вместо polling)
docker compose exec backend python manage.py setup_webhook \
    --url https://your-domain.example/telegram/webhook/
```

### Что открыть после запуска

| URL                                         | Назначение                  |
|---------------------------------------------|-----------------------------|
| http://localhost/                           | Корень nginx                |
| http://localhost/admin/                     | Django Admin                |
| http://localhost/api/docs/                  | Swagger UI                  |
| http://localhost/api/redoc/                 | Redoc                       |
| http://localhost/api/schema/                | Raw OpenAPI JSON            |
| http://localhost/health/                    | Healthcheck эндпоинты       |
| http://localhost/metrics                    | Prometheus метрики          |
| http://localhost:5555/                      | Celery Flower               |

---

## 9. Основные команды Makefile

```bash
make help              # список доступных команд
make install           # установить зависимости (для локальной разработки)

# Инфраструктура (docker compose)
make up                # поднять все сервисы (build + up -d)
make down              # остановить и удалить контейнеры
make logs              # стрим логов всех сервисов
make ps                # статус сервисов
make build             # пересобрать образы
make rebuild           # пересобрать без кэша

# Django
make migrate           # применить миграции
make makemigrations    # сгенерировать миграции
make run               # dev-сервер (runserver 0.0.0.0:8000)
make shell             # shell_plus с автоимпортом моделей
make collectstatic     # собрать статику

# Celery
make worker            # запустить worker
make beat              # запустить beat

# Telegram
make polling           # long-polling режим (для разработки)
make webhook           # установить webhook (из TELEGRAM_WEBHOOK_URL)

# Плагины
make register-plugins  # зарегистрировать встроенные плагины в БД

# Качество кода
make test              # pytest со settings.test
make lint              # ruff + black --check + isort --check
make format            # black + isort (автоформат)
```

---

## 10. Ручной запуск backend и Telegram-бота

Если вы не хотите использовать Docker, проект можно поднять напрямую:

```bash
# 0. Требуется Python 3.12+, PostgreSQL 14+, Redis 7+
cd backend

# 1. Виртуальное окружение
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 2. Зависимости
pip install -r requirements/development.txt

# 3. Переменные окружения
cp .env.example .env
# отредактируйте DATABASE_URL, REDIS_URL, OPENAI_API_KEY, TELEGRAM_BOT_TOKEN

# 4. Миграции, статика, плагины
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py register_plugins

# 5. Запуск (в разных терминалах)
python manage.py runserver 0.0.0.0:8000     # REST + Admin
daphne -b 0.0.0.0 -p 8001 config.asgi:application   # WebSocket
celery -A config worker -l info             # очередь задач
celery -A config beat -l info               # расписание
python manage.py run_polling                # Telegram (либо setup_webhook)
```

Для одновременного запуска нескольких процессов на Windows удобно использовать
PowerShell tabs или `concurrently`/`honcho` под Linux.

---

## 11. Конфигурация и переменные окружения

Все настройки читаются через `django-environ` из файла `.env`. Полный шаблон —
[`backend/.env.example`](backend/.env.example). Ключевые группы:

### Django ядро
| Переменная               | По умолчанию                         | Описание                                       |
|--------------------------|--------------------------------------|------------------------------------------------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.development`        | Используемый модуль настроек                   |
| `DJANGO_SECRET_KEY`      | —                                    | Секретный ключ Django (обязательно)            |
| `DEBUG`                  | `false`                              | Режим отладки                                  |
| `DJANGO_ALLOWED_HOSTS`   | `*`                                  | Список доменов через запятую                   |
| `LANGUAGE_CODE`          | `ru`                                 | Язык интерфейса                                |
| `TIME_ZONE`              | `Asia/Tashkent`                      | Часовой пояс                                   |

### База данных и кэш
| Переменная             | Описание                                                              |
|------------------------|-----------------------------------------------------------------------|
| `DATABASE_URL`         | DSN PostgreSQL: `postgres://user:pass@host:5432/dbname`               |
| `CONN_MAX_AGE`         | Время жизни DB-соединения (сек)                                       |
| `REDIS_URL`            | URL Redis для кэша и channel layer                                    |
| `CELERY_BROKER_URL`    | URL Redis для очередей                                                |
| `CELERY_RESULT_BACKEND`| `django-db` или `redis://...`                                         |

### Аутентификация и безопасность
| Переменная             | Описание                                            |
|------------------------|-----------------------------------------------------|
| `JWT_ACCESS_MINUTES`   | TTL access-токена (мин)                             |
| `JWT_REFRESH_DAYS`     | TTL refresh-токена (дней)                           |
| `CORS_ALLOWED_ORIGINS` | Список origin'ов для веб-клиента                    |

### Telegram
| Переменная                  | Описание                                                |
|-----------------------------|---------------------------------------------------------|
| `TELEGRAM_BOT_TOKEN`        | Токен бота, выданный @BotFather (обязательно)           |
| `TELEGRAM_WEBHOOK_URL`      | Полный URL webhook (для production)                     |
| `TELEGRAM_WEBHOOK_SECRET`   | Секрет, передаваемый в заголовке Telegram               |
| `TELEGRAM_ADMIN_IDS`        | Список Telegram-ID администраторов через запятую        |
| `TELEGRAM_ALLOWED_IDS`      | `*` или allow-list пользователей                        |

### AI-провайдеры
| Переменная             | Описание                                            |
|------------------------|-----------------------------------------------------|
| `OPENAI_API_KEY`       | Ключ OpenAI                                         |
| `OPENAI_BASE_URL`      | Можно указать прокси/OpenAI-совместимый шлюз        |
| `OPENAI_MODEL`         | Базовая чат-модель (`gpt-4o-mini` по умолчанию)     |
| `OPENAI_VISION_MODEL`  | Модель Vision                                       |
| `OPENAI_IMAGE_MODEL`   | Модель генерации изображений (`dall-e-3`)           |
| `OPENAI_TTS_MODEL`     | Модель TTS (`tts-1`)                                |
| `OPENAI_WHISPER_MODEL` | Модель распознавания речи (`whisper-1`)             |
| `ANTHROPIC_API_KEY`    | Ключ Claude                                         |
| `GOOGLE_AI_API_KEY`    | Ключ Google Generative AI                           |

### Платежи и наблюдаемость
| Переменная                 | Описание                              |
|----------------------------|---------------------------------------|
| `STRIPE_PUBLIC_KEY`        | Публичный ключ Stripe                 |
| `STRIPE_SECRET_KEY`        | Секретный ключ Stripe                 |
| `STRIPE_WEBHOOK_SECRET`    | Секрет вебхука Stripe                 |
| `SENTRY_DSN`               | DSN Sentry для ошибок и трасс         |
| `SENTRY_TRACES_RATE`       | Доля трасс (`0.0`–`1.0`)              |
| `SENTRY_PROFILES_RATE`     | Доля профайлов                        |

---

## 12. API, очереди и интеграции

### REST API

Все эндпоинты под префиксом `/api/v1/`. Аутентификация — одним из:

- `Authorization: Bearer <JWT>` — стандартный поток DRF SimpleJWT.
- `Authorization: Token <api_key>` — программный доступ через API-ключ.
- `X-Telegram-Init-Data: <signed-payload>` — Telegram Mini App.

Ключевые группы маршрутов:

| Группа               | Описание                                                |
|----------------------|---------------------------------------------------------|
| `/auth/`             | `register`, `login`, `token/refresh`, `token/verify`    |
| `/users/me/`         | Профиль и настройки текущего пользователя               |
| `/conversations/`    | CRUD диалогов, `POST /conversations/chat` для AI-ответа |
| `/messages/`         | Просмотр сообщений и метаданных                         |
| `/attachments/`      | Файлы, прикреплённые к сообщениям                       |
| `/ai/models/`        | Каталог моделей и их прайсинг                           |
| `/ai/images/`        | Генерация изображений                                   |
| `/ai/transcribe/`    | Распознавание речи                                      |
| `/ai/tts/`           | Синтез речи                                             |
| `/plans/`            | Тарифные планы                                          |
| `/subscriptions/`    | Подписки пользователя                                   |
| `/invoices/`         | Счета                                                   |
| `/payments/`         | Платежи                                                 |
| `/credits/transactions/` | История кредитных операций                          |
| `/plugins/`          | Список и вызов плагинов                                 |
| `/analytics/events/` | Сырые события (плюс `summary?days=30`)                  |
| `/notifications/`    | История уведомлений                                     |
| `/broadcasts/`       | Управление массовыми рассылками (admin)                 |
| `/keys/`             | Управление API-ключами                                  |
| `/audit/`            | Журнал аудита (admin)                                   |

### WebSocket

- `ws://host/ws/chat/<conversation_id>/` — двусторонний чат, события `ready`, `chunk`, `message`.
- `ws://host/ws/notifications/` — персональный канал, событие `notification`.

### Очереди Celery

| Очередь    | Что обрабатывает                                            |
|------------|-------------------------------------------------------------|
| `default`  | Биллинг, аналитика, уведомления                             |
| `telegram` | Обработка webhook-обновлений, рассылка в Telegram           |
| `ai`       | Долгие вызовы провайдеров AI, генерация сводок диалогов     |

Регулярные задачи (`config/celery.py → beat_schedule`):

- `reset_daily_usage` — каждый день в 00:05
- `renew_subscriptions` — каждый час в 15-ю минуту
- `cleanup_old_conversations` — ежедневно в 03:30
- `send_daily_reports` — ежедневно в 08:00
- `refresh_plugin_cache` — каждые 30 минут

### Интеграции

- **Stripe** — счета, webhook платежей (`/billing/stripe/webhook/`).
- **Telegram Bot API** — webhook + polling, отправка фото/голоса.
- **OpenAI / Anthropic / Google** — заменяемые адаптеры `BaseProvider`.
- **DuckDuckGo / Open-Meteo / Wolfram / Spotify / YouTube** — встроенные плагины.

---

## 13. Мониторинг и эксплуатация

| Аспект           | Решение                                                                    |
|------------------|----------------------------------------------------------------------------|
| Метрики          | `/metrics` (django-prometheus): запросы, БД, кэш, Celery                   |
| Логи             | structlog + JSON-форматер, готов к Loki/ELK; nginx access/error logs       |
| Ошибки           | Sentry с интеграциями Django, Celery, Redis (см. `production.py`)          |
| Очереди          | Flower (`:5555`), Celery task track started, retry с экспонентой           |
| Healthcheck      | `/health/` (`django-health-check`): db, cache, storage                     |
| Профилирование   | `django-silk` в dev, `django-debug-toolbar` в `127.0.0.1`                  |
| Аудит            | `AuditLog` + `AIRequestLog` + `PluginInvocation` + `TelegramUpdate`        |

Рекомендуемые алерты в Prometheus/Grafana:

- `http_requests_total{status=~"5.."}` > 1% от трафика
- `celery_task_failed_total` > 0 за 5 минут
- `redis_connected_clients` rapidly растёт
- `pg_stat_activity` long-running queries > 30s

---

## 14. CI/CD

Минимальный pipeline (GitHub Actions / GitLab CI) выглядит так:

```yaml
# .github/workflows/ci.yml (рекомендуемый шаблон)
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: {POSTGRES_USER: aibot, POSTGRES_PASSWORD: aibot, POSTGRES_DB: aibot}
        ports: ["5432:5432"]
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install -r backend/requirements/development.txt
      - run: cd backend && make lint
      - run: cd backend && make test
      - run: cd backend && docker build -f docker/django/Dockerfile -t neurolink-backend .
```

Pipeline для production:

1. `lint` → `test` → `build` Docker-образа с тегом коммита.
2. Push в реестр (`ghcr.io`, `Docker Hub`, `Yandex CR`).
3. Деплой через `docker compose pull && docker compose up -d` или Kubernetes manifest.
4. Авто-миграции прогоняются `entrypoint.sh` при старте контейнера.

---

## 15. Безопасность и хранение данных

### Аутентификация
- **Argon2** для хешей паролей, MD5-хешер используется только в тестах.
- **JWT** с ротацией refresh и blacklist выбывших токенов.
- **API-ключи**: префикс хранится открытым (для поиска), сам ключ — только SHA-256.
- **Telegram WebApp**: HMAC-SHA256 проверка с TTL `auth_date` 24 часа.

### Защита от атак
- `django-axes` — лимиты на попытки входа по `(username, ip)`.
- `django-ratelimit` + DRF throttling — на REST-эндпоинты.
- `SECURE_HSTS_*`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`, `X-Frame-Options: DENY` —
  включены в `production.py`.
- `SECURE_PROXY_SSL_HEADER` для работы за nginx/cloudflare.

### Данные
- PostgreSQL — основное хранилище; рекомендуем шифрование тома на уровне ОС.
- Медиа-файлы (вложения, изображения) — локально или S3/MinIO через `django-storages`.
- Кэш и брокер — Redis, отдельные базы `0` (кэш), `1` (Celery).
- Журналы (`AuditLog`, `AIRequestLog`, `PluginInvocation`, `TelegramUpdate`) — каскадная
  очистка периодической задачей.

### Соответствие требованиям
- Поддержка прав доступа RBAC и журнала действий — для GDPR/152-ФЗ.
- Возможность soft-delete пользовательских данных и анонимизации.
- Все секреты — только через переменные окружения, никогда в репозитории.

---

## 16. Роли компонентов в продакшене

| Компонент      | Роль                                                                              |
|----------------|-----------------------------------------------------------------------------------|
| `nginx`        | Внешняя точка входа, TLS-terminator, отдача `/static/` и `/media/`, маршрутизация HTTP/WS |
| `backend`      | DRF REST API, Admin, OpenAPI; держит соединения с БД/Redis, синхронная обработка       |
| `daphne`       | ASGI-сервер для Channels; принимает WebSocket-соединения и отдаёт push-уведомления     |
| `celery-worker`| Долгие задачи: вызовы AI-провайдеров, рассылки, обработка Telegram-обновлений          |
| `celery-beat`  | Планировщик cron-задач (продление подписок, отчёты, очистка)                           |
| `celery-flower`| Дашборд очередей: статусы задач, время выполнения, retry                               |
| `telegram-bot` | Long-polling (когда webhook недоступен), может быть отключён в production              |
| `postgres`     | OLTP-хранилище метаданных, аналитики, журналов                                         |
| `redis`        | Кэш Django, брокер Celery, channel layer для WebSocket                                 |

В production рекомендуется разнести компоненты по разным узлам/подам, использовать
managed PostgreSQL/Redis, выносить `media_data` в объектное хранилище и поднимать несколько
реплик `backend`/`daphne`/`celery-worker` за балансировщиком.

---

## 17. Лицензия

Проект распространяется по лицензии **GNU GPL 2.0** — см. [LICENSE](LICENSE).
Использование сторонних SDK (OpenAI, Anthropic, Stripe, Telegram) регулируется
их собственными условиями.

---

## 18. Поддержка

- **Issues и баг-репорты**: создавайте в репозитории
  [NodirOdilov/AI-Telegram-Bot](https://github.com/NodirOdilov/AI-Telegram-Bot/issues).
- **Документация API**: Swagger UI — `/api/docs/`, Redoc — `/api/redoc/`.
- **Документация бэкенда**: [`backend/README.md`](backend/README.md).
- **Контакты по интеграции и развёртыванию**: укажите в `MAINTAINERS.md` (или используйте
  контакты владельца репозитория).

---

<div align="center">

**NeuroLink** — соберите свою AI-платформу за один день и масштабируйте её до миллионов запросов.

Made with Python, Django, Channels and Celery.

</div>
