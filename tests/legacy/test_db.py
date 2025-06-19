#!/usr/bin/env python3
"""
Скрипт для тестирования базы данных
"""

import os
import sys
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Base, SessionLocal, engine
from models import RepairWork


def test_database():
    """Тестирование базы данных"""
    print("=== Тестирование базы данных ===")

    # Создаем таблицы
    print("1. Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("✓ Таблицы созданы")

    # Создаем сессию
    db = SessionLocal()

    try:
        # Очищаем таблицу для тестирования
        print("2. Очистка таблицы...")
        db.query(RepairWork).delete()
        db.commit()
        print("✓ Таблица очищена")

        # Создаем тестовую запись
        print("3. Создание тестовой записи...")
        test_work = RepairWork(
            location="49.9935,36.2304",
            description="Тестовая ремонтная работа",
            start_datetime=datetime.now(),
            end_datetime=None,
        )
        db.add(test_work)
        db.commit()
        db.refresh(test_work)
        print(f"✓ Создана запись с ID: {test_work.id}")

        # Проверяем чтение
        print("4. Чтение записей...")
        works = db.query(RepairWork).all()
        print(f"✓ Найдено записей: {len(works)}")

        for work in works:
            print(f"  - ID: {work.id}, Описание: {work.description}")
            print(f"    Локация: {work.location}")
            print(f"    Начало: {work.start_datetime}")

        # Создаем еще одну запись (маршрут)
        print("5. Создание записи маршрута...")
        route_work = RepairWork(
            start_location="49.9935,36.2304",
            end_location="49.9945,36.2314",
            description="Тестовый маршрут",
            start_datetime=datetime.now(),
        )
        db.add(route_work)
        db.commit()
        db.refresh(route_work)
        print(f"✓ Создана запись маршрута с ID: {route_work.id}")

        # Финальная проверка
        print("6. Финальная проверка...")
        all_works = db.query(RepairWork).all()
        print(f"✓ Всего записей в базе: {len(all_works)}")

        print("\n=== Тест успешно завершен ===")
        return True

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def check_database_file():
    """Проверка файла базы данных"""
    print("=== Проверка файла базы данных ===")

    db_path = "./db/app.db"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✓ Файл базы данных существует: {db_path}")
        print(f"  Размер: {size} байт")
    else:
        print(f"❌ Файл базы данных не найден: {db_path}")
        print("  Создаем директорию...")
        os.makedirs("./db", exist_ok=True)


if __name__ == "__main__":
    check_database_file()
    success = test_database()

    if success:
        print("\n🎉 База данных работает корректно!")
    else:
        print("\n💥 Есть проблемы с базой данных!")
        sys.exit(1)
