# Удобные команды разработки и деплоя
# ===================================
PYTHON ?= python
COMPOSE ?= docker compose

.PHONY: help install migrate makemigrations run shell test lint format \
        worker beat polling webhook collectstatic register-plugins \
        up down logs ps build rebuild

help:
	@echo "Команды:"
	@echo "  make install            установить зависимости разработки"
	@echo "  make migrate            применить миграции"
	@echo "  make makemigrations     создать новые миграции"
	@echo "  make run                запустить dev-сервер"
	@echo "  make worker             запустить Celery worker"
	@echo "  make beat               запустить Celery beat"
	@echo "  make polling            запустить Telegram бот в режиме polling"
	@echo "  make webhook            установить Telegram webhook"
	@echo "  make test               запустить тесты"
	@echo "  make lint               запустить линтеры"
	@echo "  make format             отформатировать код"
	@echo "  make up                 поднять docker-compose"
	@echo "  make down               остановить docker-compose"

install:
	$(PYTHON) -m pip install -r requirements/development.txt

migrate:
	$(PYTHON) manage.py migrate

makemigrations:
	$(PYTHON) manage.py makemigrations

run:
	$(PYTHON) manage.py runserver 0.0.0.0:8000

shell:
	$(PYTHON) manage.py shell_plus

worker:
	celery -A config worker -l info

beat:
	celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

polling:
	$(PYTHON) manage.py run_polling

webhook:
	$(PYTHON) manage.py setup_webhook

collectstatic:
	$(PYTHON) manage.py collectstatic --noinput

register-plugins:
	$(PYTHON) manage.py register_plugins

test:
	DJANGO_SETTINGS_MODULE=config.settings.test pytest -q

lint:
	ruff check apps config
	black --check apps config
	isort --check-only apps config

format:
	black apps config
	isort apps config

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) build --no-cache
