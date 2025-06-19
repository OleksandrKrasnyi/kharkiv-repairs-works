import os
from datetime import datetime

import aiohttp
import uvicorn
from database import engine, get_db
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fuzzywuzzy import fuzz
from models import Base, RepairWork, WorkType
from pydantic import BaseModel
from sqlalchemy.orm import Session

app = FastAPI()

# Создание директории для базы данных
os.makedirs("db", exist_ok=True)

# Создание директорий для статических файлов
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

# Добавление CORS middleware - ИСПРАВЛЕНО
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic модели для типов работ
class WorkTypeCreate(BaseModel):
    name: str
    description: str | None = None
    color: str | None = "#667eea"


class WorkTypeResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    color: str


# Pydantic модели для поиска улиц
class StreetSearchResult(BaseModel):
    display_name: str
    lat: float
    lon: float
    importance: float
    boundingbox: list[float]


# Pydantic модель для валидации ремонтных работ
class RepairWorkCreate(BaseModel):
    location: str | None = None
    start_location: str | None = None
    end_location: str | None = None
    description: str | None = None
    start_datetime: str  # Будет строкой из HTML datetime-local
    end_datetime: str | None = None
    work_type_id: int | None = None


class RepairWorkResponse(BaseModel):
    id: int
    location: str | None = None
    start_location: str | None = None
    end_location: str | None = None
    description: str | None = None
    start_datetime: str
    end_datetime: str | None = None
    work_type_id: int | None = None
    work_type: WorkTypeResponse | None = None


# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)


# Эндпоинты для управления типами работ
@app.get("/work-types/", response_model=list[WorkTypeResponse])
async def get_work_types(db: Session = Depends(get_db)):
    try:
        print("=== ЗАПРОС НА ПОЛУЧЕНИЕ ТИПОВ РАБОТ ===")
        work_types = db.query(WorkType).all()
        print(f"Найдено типов работ в БД: {len(work_types)}")

        result = []
        for wt in work_types:
            type_data = {
                "id": wt.id,
                "name": wt.name,
                "description": wt.description,
                "color": wt.color,
            }
            result.append(type_data)
            print(f"Тип работ ID {wt.id}: {wt.name}")

        return result
    except Exception as e:
        print(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ТИПОВ РАБОТ: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Ошибка при получении типов работ: {str(e)}"
        )


@app.post("/work-types/", response_model=WorkTypeResponse)
async def create_work_type(work_type: WorkTypeCreate, db: Session = Depends(get_db)):
    try:
        print("=== СОЗДАНИЕ ТИПА РАБОТ ===")
        print(f"Данные: {work_type.dict()}")

        # Проверяем, не существует ли уже такой тип
        existing = db.query(WorkType).filter(WorkType.name == work_type.name).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="Тип работ с таким именем уже существует"
            )

        db_work_type = WorkType(
            name=work_type.name,
            description=work_type.description,
            color=work_type.color,
        )

        db.add(db_work_type)
        db.commit()
        db.refresh(db_work_type)

        print(f"УСПЕШНО СОЗДАН ТИП РАБОТ с ID: {db_work_type.id}")

        return WorkTypeResponse(
            id=db_work_type.id,
            name=db_work_type.name,
            description=db_work_type.description,
            color=db_work_type.color,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        import traceback

        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")


@app.delete("/work-types/{work_type_id}")
async def delete_work_type(work_type_id: int, db: Session = Depends(get_db)):
    try:
        print(f"=== УДАЛЕНИЕ ТИПА РАБОТ ID: {work_type_id} ===")
        work_type = db.query(WorkType).filter(WorkType.id == work_type_id).first()
        if work_type:
            # Проверяем, не используется ли этот тип в ремонтных работах
            repair_works_count = (
                db.query(RepairWork)
                .filter(RepairWork.work_type_id == work_type_id)
                .count()
            )
            if repair_works_count > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Нельзя удалить тип работ, используемый в {repair_works_count} ремонтных работах",
                )

            db.delete(work_type)
            db.commit()
            print(f"УСПЕШНО УДАЛЕН тип работ с ID {work_type_id}")
            return {"message": "Work type deleted"}
        else:
            print(f"Тип работ с ID {work_type_id} НЕ НАЙДЕН")
            raise HTTPException(status_code=404, detail="Work type not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"ОШИБКА ПРИ УДАЛЕНИИ ТИПА РАБОТ: {str(e)}")
        import traceback

        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении: {str(e)}")


@app.post("/repair-works/", response_model=RepairWorkResponse)
async def add_repair_work(repair_work: RepairWorkCreate, db: Session = Depends(get_db)):
    print("=== ПОЛУЧЕН ЗАПРОС ===")
    print(f"Данные: {repair_work.dict()}")

    try:
        # Валидация: должна быть либо location, либо start_location и end_location
        if not repair_work.location and not (
            repair_work.start_location and repair_work.end_location
        ):
            print("ОШИБКА: Не указано местоположение")
            raise HTTPException(
                status_code=400,
                detail="Необходимо указать либо location, либо start_location и end_location",
            )

        # Проверяем существование типа работ, если указан
        work_type = None
        if repair_work.work_type_id:
            work_type = (
                db.query(WorkType)
                .filter(WorkType.id == repair_work.work_type_id)
                .first()
            )
            if not work_type:
                raise HTTPException(
                    status_code=400, detail="Указанный тип работ не найден"
                )

        # Преобразование строки datetime в объект datetime
        print(f"Преобразование даты начала: {repair_work.start_datetime}")
        start_dt = datetime.fromisoformat(repair_work.start_datetime)
        end_dt = None
        if repair_work.end_datetime:
            print(f"Преобразование даты окончания: {repair_work.end_datetime}")
            end_dt = datetime.fromisoformat(repair_work.end_datetime)

        print("Создание объекта RepairWork...")
        db_repair_work = RepairWork(
            location=repair_work.location,
            start_location=repair_work.start_location,
            end_location=repair_work.end_location,
            description=repair_work.description,
            start_datetime=start_dt,
            end_datetime=end_dt,
            work_type_id=repair_work.work_type_id,
        )

        print("Добавление в БД...")
        db.add(db_repair_work)
        db.commit()
        db.refresh(db_repair_work)

        print(f"УСПЕШНО СОЗДАНА ЗАПИСЬ с ID: {db_repair_work.id}")

        result = RepairWorkResponse(
            id=db_repair_work.id,
            location=db_repair_work.location,
            start_location=db_repair_work.start_location,
            end_location=db_repair_work.end_location,
            description=db_repair_work.description,
            start_datetime=db_repair_work.start_datetime.isoformat(),
            end_datetime=db_repair_work.end_datetime.isoformat()
            if db_repair_work.end_datetime
            else None,
            work_type_id=db_repair_work.work_type_id,
            work_type=WorkTypeResponse(
                id=work_type.id,
                name=work_type.name,
                description=work_type.description,
                color=work_type.color,
            )
            if work_type
            else None,
        )

        print(f"Возвращаемый результат: {result.dict()}")
        return result

    except ValueError as e:
        print(f"ОШИБКА ВАЛИДАЦИИ: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Неверный формат даты: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        print(f"Тип исключения: {type(e)}")
        import traceback

        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")


@app.get("/repair-works/")
async def get_repair_works(db: Session = Depends(get_db)):
    try:
        print("=== ЗАПРОС НА ПОЛУЧЕНИЕ ВСЕХ РАБОТ ===")
        repair_works = db.query(RepairWork).all()
        print(f"Найдено работ в БД: {len(repair_works)}")

        result = []
        for rw in repair_works:
            work_type_data = None
            if rw.work_type:
                work_type_data = {
                    "id": rw.work_type.id,
                    "name": rw.work_type.name,
                    "description": rw.work_type.description,
                    "color": rw.work_type.color,
                }

            work_data = {
                "id": rw.id,
                "location": rw.location,
                "start_location": rw.start_location,
                "end_location": rw.end_location,
                "description": rw.description,
                "start_datetime": rw.start_datetime.isoformat()
                if rw.start_datetime
                else None,
                "end_datetime": rw.end_datetime.isoformat()
                if rw.end_datetime
                else None,
                "work_type_id": rw.work_type_id,
                "work_type": work_type_data,
            }
            result.append(work_data)
            print(f"Работа ID {rw.id}: {rw.description}")

        return result
    except Exception as e:
        print(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ДАННЫХ: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Ошибка при получении данных: {str(e)}"
        )


@app.delete("/repair-works/{repair_id}")
async def delete_repair_work(repair_id: int, db: Session = Depends(get_db)):
    try:
        print(f"=== УДАЛЕНИЕ РАБОТЫ ID: {repair_id} ===")
        repair_work = db.query(RepairWork).filter(RepairWork.id == repair_id).first()
        if repair_work:
            db.delete(repair_work)
            db.commit()
            print(f"УСПЕШНО УДАЛЕНА работа с ID {repair_id}")
            return {"message": "Repair work deleted"}
        else:
            print(f"Работа с ID {repair_id} НЕ НАЙДЕНА")
            raise HTTPException(status_code=404, detail="Repair work not found")
    except Exception as e:
        print(f"ОШИБКА ПРИ УДАЛЕНИИ: {str(e)}")
        import traceback

        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении: {str(e)}")


# Добавляем маршрут для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    return FileResponse("index.html")


# Добавляем простой тестовый маршрут
@app.get("/test")
async def test():
    return {"message": "Backend is working!", "timestamp": datetime.now().isoformat()}


# Добавляем маршрут для проверки БД
@app.get("/db-test")
async def db_test(db: Session = Depends(get_db)):
    try:
        # Проверяем подключение к БД
        count = db.query(RepairWork).count()
        return {"message": "Database connection OK", "total_works": count}
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}


# Эндпоинт для поиска улиц
@app.get("/search-streets/", response_model=list[StreetSearchResult])
async def search_streets(q: str = Query(..., description="Поисковый запрос для улицы")):
    try:
        print("=== ПОИСК УЛИЦ ===")
        print(f"Запрос: {q}")

        # Создаем несколько вариантов поискового запроса для Харькова
        search_queries = [
            f"{q}, Харків, Україна",
            f"{q}, Kharkiv, Ukraine",
            f"улица {q}, Харків",
            f"street {q}, Kharkiv",
        ]

        all_results = []

        async with aiohttp.ClientSession() as session:
            for query in search_queries:
                try:
                    url = "https://nominatim.openstreetmap.org/search"
                    params = {
                        "q": query,
                        "format": "json",
                        "limit": 10,
                        "countrycodes": "ua",
                        "bounded": 1,
                        "viewbox": "35.8,49.8,36.6,50.2",  # Примерные границы Харькова
                        "addressdetails": 1,
                    }
                    headers = {"User-Agent": "Kharkiv Repair Works App"}

                    async with session.get(
                        url, params=params, headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            for item in data:
                                # Фильтруем только улицы в Харькове
                                if (
                                    "харків" in item.get("display_name", "").lower()
                                    or "kharkiv" in item.get("display_name", "").lower()
                                ):
                                    result = StreetSearchResult(
                                        display_name=item["display_name"],
                                        lat=float(item["lat"]),
                                        lon=float(item["lon"]),
                                        importance=float(item.get("importance", 0)),
                                        boundingbox=[
                                            float(x) for x in item["boundingbox"]
                                        ],
                                    )
                                    all_results.append(result)
                except Exception as e:
                    print(f"Ошибка при запросе '{query}': {str(e)}")
                    continue

        # Удаляем дубликаты по координатам
        unique_results = []
        seen_coords = set()

        for result in all_results:
            coord_key = (round(result.lat, 4), round(result.lon, 4))
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_results.append(result)

        # Сортируем по важности и релевантности
        def calculate_relevance(result):
            # Используем fuzzy matching для определения релевантности
            name_relevance = fuzz.partial_ratio(q.lower(), result.display_name.lower())
            return result.importance * 100 + name_relevance

        unique_results.sort(key=calculate_relevance, reverse=True)

        # Ограничиваем результаты
        final_results = unique_results[:10]

        print(f"Найдено улиц: {len(final_results)}")
        for i, result in enumerate(final_results[:3]):
            print(f"  {i + 1}. {result.display_name}")

        return final_results

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА ПОИСКА: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {str(e)}")


if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК СЕРВЕРА")
    print("=" * 50)
    print("Веб-интерфейс: http://localhost:8000")
    print("API документация: http://localhost:8000/docs")
    print("Тест бекенда: http://localhost:8000/test")
    print("Тест БД: http://localhost:8000/db-test")
    print("=" * 50)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
