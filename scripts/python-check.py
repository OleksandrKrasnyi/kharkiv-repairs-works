#!/usr/bin/env python3
"""
Скрипт для проверки качества Python кода
Аналог frontend-check для Python
"""

import os
import subprocess
import sys


def run_command(cmd, description):
    """Запуск команды с выводом результата"""
    print(f"\n🔍 {description}")
    print("=" * 60)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"❌ Ошибка выполнения команды: {e}")
        return False


def main():
    """Основная функция проверки"""
    print("🐍 ПРОВЕРКА КАЧЕСТВА PYTHON КОДА")
    print("=" * 60)

    # Проверяем, что мы в корневой папке проекта
    if not os.path.exists("pyproject.toml"):
        print(
            "❌ Не найден pyproject.toml. Запустите скрипт из корневой папки проекта."
        )
        sys.exit(1)

    success = True

    # 1. Ruff - линтинг
    print("\n📋 1. RUFF ЛИНТИНГ")
    ruff_success = run_command(
        "uv run ruff check", "Проверка качества кода с помощью ruff"
    )
    if not ruff_success:
        success = False
        print("❌ Найдены проблемы качества кода")

        # Показываем статистику
        print("\n📊 Статистика ошибок:")
        run_command("uv run ruff check --statistics", "Статистика по типам ошибок")
    else:
        print("✅ Код соответствует стандартам качества!")

    # 2. MyPy - проверка типов
    print("\n🔍 2. MYPY - ПРОВЕРКА ТИПОВ")
    mypy_success = run_command(
        "uv run mypy --config-file pyproject.toml backend/",
        "Проверка типов с помощью mypy",
    )
    if not mypy_success:
        success = False
        print("❌ Найдены проблемы с типизацией")
    else:
        print("✅ Типизация корректна!")

    # 3. Итоговый результат
    print("\n" + "=" * 60)
    if success:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("✅ Код готов к коммиту")
    else:
        print("❌ НАЙДЕНЫ ПРОБЛЕМЫ")
        print(
            "🔧 Запустите 'python scripts/python-fix.py' для автоматического исправления"
        )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
