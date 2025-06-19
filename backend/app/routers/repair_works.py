"""
Роутер для управления ремонтными работами
"""

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.repair_work import (
    RepairWorkCreate,
    RepairWorkDetailed,
    RepairWorkResponse,
    RepairWorkUpdate,
    WorkStatus,
)
from ..services.repair_work_service import RepairWorkService

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[RepairWorkDetailed])
async def get_repair_works(
    status: WorkStatus | None = Query(None, description="Фильтр по статусу"),
    work_type_id: int | None = Query(None, description="Фильтр по типу работы"),
    start_date: datetime | None = Query(None, description="Фильтр по дате начала (с)"),
    end_date: datetime | None = Query(None, description="Фильтр по дате начала (до)"),
    is_completed: bool | None = Query(None, description="Фильтр завершенных работ"),
    limit: int = Query(
        100, ge=1, le=500, description="Максимальное количество результатов"
    ),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    db: Session = Depends(get_db),
):
    """
    Получить список ремонтных работ

    - **status**: фильтр по статусу работы
    - **work_type_id**: фильтр по типу работы
    - **start_date**: фильтр по дате начала (с указанной даты)
    - **end_date**: фильтр по дате начала (до указанной даты)
    - **is_completed**: фильтр завершенных работ (True - только завершенные, False - только незавершенные)
    - **limit**: максимальное количество результатов
    - **offset**: смещение для пагинации
    """
    logger.info(
        "Getting repair works",
        status=status,
        work_type_id=work_type_id,
        start_date=start_date,
        end_date=end_date,
        is_completed=is_completed,
    )

    service = RepairWorkService(db)
    repair_works = service.get_all(
        status=status,
        work_type_id=work_type_id,
        start_date=start_date,
        end_date=end_date,
        is_completed=is_completed,
        limit=limit,
        offset=offset,
    )

    return repair_works


@router.get("/{repair_work_id}", response_model=RepairWorkDetailed)
async def get_repair_work(repair_work_id: int, db: Session = Depends(get_db)):
    """
    Получить ремонтную работу по ID
    """
    logger.info("Getting repair work by ID", repair_work_id=repair_work_id)

    service = RepairWorkService(db)
    repair_work = service.get_by_id(repair_work_id)

    if not repair_work:
        raise HTTPException(status_code=404, detail="Ремонтная работа не найдена")

    return repair_work


@router.post("/", response_model=RepairWorkResponse)
async def create_repair_work(
    repair_work_data: RepairWorkCreate, db: Session = Depends(get_db)
):
    """
    Создать новую ремонтную работу
    """
    logger.info("Creating repair work")

    service = RepairWorkService(db)
    repair_work = service.create(repair_work_data)

    return repair_work


@router.put("/{repair_work_id}", response_model=RepairWorkResponse)
async def update_repair_work(
    repair_work_id: int,
    repair_work_data: RepairWorkUpdate,
    db: Session = Depends(get_db),
):
    """
    Обновить ремонтную работу
    """
    logger.info("Updating repair work", repair_work_id=repair_work_id)

    service = RepairWorkService(db)
    repair_work = service.update(repair_work_id, repair_work_data)

    if not repair_work:
        raise HTTPException(status_code=404, detail="Ремонтная работа не найдена")

    return repair_work


@router.delete("/{repair_work_id}")
async def delete_repair_work(repair_work_id: int, db: Session = Depends(get_db)):
    """
    Удалить ремонтную работу
    """
    logger.info("Deleting repair work", repair_work_id=repair_work_id)

    service = RepairWorkService(db)

    # Проверяем существование работы
    existing_work = service.get_by_id(repair_work_id)
    if not existing_work:
        raise HTTPException(status_code=404, detail="Ремонтная работа не найдена")

    service.delete(repair_work_id)

    return {"message": "Ремонтная работа успешно удалена"}
