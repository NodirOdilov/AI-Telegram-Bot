#!/bin/sh
# Точка входа контейнера: миграции, статика, запуск переданной команды.
set -e

echo "==> Ожидание PostgreSQL..."
python << 'PY'
import os, time, sys, socket
host = os.environ.get("POSTGRES_HOST", "postgres")
port = int(os.environ.get("POSTGRES_PORT", 5432))
deadline = time.time() + 60
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print("postgres готов")
            sys.exit(0)
    except OSError:
        time.sleep(1)
sys.exit(1)
PY

echo "==> Применяем миграции..."
python manage.py migrate --noinput

echo "==> Собираем статику..."
python manage.py collectstatic --noinput || true

echo "==> Регистрируем встроенные плагины..."
python manage.py register_plugins || true

echo "==> Запуск: $@"
exec "$@"
