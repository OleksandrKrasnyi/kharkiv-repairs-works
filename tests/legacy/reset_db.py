#!/usr/bin/env python3
"""
Скрипт для полного сброса базы данных
"""

import os
import sys
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SQLALCHEMY_DATABASE_URL, Base
from models import RepairWork, WorkType


def reset_database():
    """Полный сброс базы данных"""
    print("=== Сброс базы данных ===")

    # Удаляем файл базы данных, если он существует
    db_file = "./db/app.db"
    if os.path.exists(db_file):
        print(f"1. Удаление старой базы данных: {db_file}")
        try:
            os.remove(db_file)
            print("✓ Старая база данных удалена")
        except Exception as e:
            print(f"❌ Ошибка при удалении: {e}")
            return False
    else:
        print("1. Старая база данных не найдена")

    # Создаем директорию для БД, если не существует
    db_dir = os.path.dirname(db_file)
    if not os.path.exists(db_dir):
        print(f"2. Создание директории: {db_dir}")
        os.makedirs(db_dir, exist_ok=True)
        print("✓ Директория создана")
    else:
        print("2. Директория уже существует")

    # Создаем новую БД
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    print("✓ База данных создана")

    # Создаем сессию
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Добавляем типы работ по умолчанию
        default_work_types = [
            WorkType(
                name="Ремонт дорожного покрытия",
                description="Асфальтирование, ямочный ремонт, укладка нового покрытия",
                color="#ff6b6b",
            ),
            WorkType(
                name="Ремонт тротуарів",
                description="Заміна плитки, вирівнювання, ремонт бордюрів",
                color="#4ecdc4",
            ),
            WorkType(
                name="Водопровідні роботи",
                description="Ремонт водопроводу, заміна труб, встановлення лічильників",
                color="#45b7d1",
            ),
            WorkType(
                name="Електромережі",
                description="Ремонт ліній електропередач, встановлення освітлення",
                color="#f9ca24",
            ),
            WorkType(
                name="Каналізація",
                description="Ремонт каналізаційних систем, прочищення засорів",
                color="#8b4513",
            ),
            WorkType(
                name="Озеленення",
                description="Посадка дерев, облаштування клумб, підрізка",
                color="#2ed573",
            ),
            WorkType(
                name="Дорожня розмітка",
                description="Нанесення розмітки, встановлення знаків",
                color="#333333",
            ),
            WorkType(
                name="Благоустрій",
                description="Встановлення лавок, урн, дитячих майданчиків",
                color="#ff9ff3",
            ),
        ]

        for work_type in default_work_types:
            db.add(work_type)

        db.commit()
        print(f"✓ Додано {len(default_work_types)} типів робіт за замовчуванням")

        # Добавляем несколько примеров ремонтных работ
        sample_works = [
            RepairWork(
                location="49.991500,36.231400",
                description="Ремонт дорожнього покриття на вул. Сумська",
                start_datetime=datetime(2024, 1, 15, 9, 0),
                end_datetime=datetime(2024, 1, 20, 18, 0),
                work_type_id=1,
            ),
            RepairWork(
                start_location="49.988200,36.233100",
                end_location="49.990100,36.235800",
                description="Заміна водопровідних труб на вул. Пушкінська",
                start_datetime=datetime(2024, 1, 10, 8, 0),
                work_type_id=3,
            ),
            RepairWork(
                location="49.996800,36.228900",
                description="Встановлення нових ліхтарів у парку Горького",
                start_datetime=datetime(2024, 1, 5, 10, 0),
                end_datetime=datetime(2024, 1, 8, 16, 0),
                work_type_id=4,
            ),
        ]

        for work in sample_works:
            db.add(work)

        db.commit()
        print(f"✓ Додано {len(sample_works)} прикладів ремонтних робіт")

    except Exception as e:
        print(f"❌ Помилка при ініціалізації даних: {str(e)}")
        db.rollback()
    finally:
        db.close()

    print("\n=== База данных успешно сброшена ===")
    print("=" * 50)
    print("БАЗА ДАННЫХ УСПІШНО ІНІЦІАЛІЗОВАНА!")
    print("=" * 50)
    print("Тепер ви можете запустити сервер командою:")
    print("python main.py")
    print("=" * 50)
    return True


def create_test_data():
    """Создание тестовых данных"""
    print("\n=== Создание тестовых данных ===")

    # Создаем подключение к БД
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        # Создаем тестовую точку
        print("1. Создание тестовой точки...")
        point_work = RepairWork(
            location="49.9935,36.2304",
            description="Тестовая ремонтная работа - точка",
            start_datetime=datetime.now(),
        )
        db.add(point_work)

        # Создаем тестовый маршрут
        print("2. Создание тестового маршрута...")
        route_work = RepairWork(
            start_location="49.9935,36.2304",
            end_location="49.9945,36.2314",
            description="Тестовая ремонтная работа - маршрут",
            start_datetime=datetime.now(),
        )
        db.add(route_work)

        db.commit()
        print("✓ Тестовые данные созданы")

        # Проверяем созданные данные
        all_works = db.query(RepairWork).all()
        print(f"✓ Всего записей в базе: {len(all_works)}")

        for work in all_works:
            print(f"  - ID: {work.id}")
            print(f"    Описание: {work.description}")
            if work.location:
                print(f"    Точка: {work.location}")
            else:
                print(f"    Маршрут: {work.start_location} -> {work.end_location}")
            print(f"    Начало: {work.start_datetime}")

        return True

    except Exception as e:
        print(f"❌ Ошибка при создании тестовых данных: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("🔄 Начинаем сброс базы данных...")

    # Сбрасываем базу данных
    if reset_database():
        print("\n" + "=" * 50)

        # Создаем тестовые данные
        if create_test_data():
            print("\n🎉 База данных успешно сброшена и заполнена тестовыми данными!")
            print("\nТеперь можно запускать сервер:")
            print("python main.py")
        else:
            print("\n⚠️ База данных сброшена, но не удалось создать тестовые данные")
    else:
        print("\n💥 Ошибка при сбросе базы данных!")
        sys.exit(1)
