#!/usr/bin/env python
"""Утилита командной строки Django для административных задач."""
import os
import sys
from pathlib import Path


def main() -> None:
    """Точка входа управляющей утилиты."""
    # Корневая директория добавляется в путь поиска модулей, чтобы можно было
    # использовать пакет ``apps`` без явного указания префикса.
    base_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(base_dir))
    sys.path.insert(0, str(base_dir / "apps"))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не удалось импортировать Django. Убедитесь, что он установлен и "
            "активировано виртуальное окружение."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
