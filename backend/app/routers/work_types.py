"""
Роутер для управления типами работ
"""

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.work_type import (
    WorkTypeCreate,
    WorkTypeResponse,
    WorkTypeUpdate,
    WorkTypeWithStats,
)
from ..services import WorkTypeService

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[WorkTypeResponse])
async def get_work_types(
    include_inactive: bool = Query(False, description="Включать неактивные типы работ"),
    db: Session = Depends(get_db),
):
    """
    Получить все типы работ

    - **include_inactive**: включать ли неактивные типы работ
    """
    logger.info("Getting work types", include_inactive=include_inactive)

    service = WorkTypeService(db)
    work_types = service.get_all(include_inactive=include_inactive)

    return work_types


@router.get("/{work_type_id}", response_model=WorkTypeWithStats)
async def get_work_type(work_type_id: int, db: Session = Depends(get_db)):
    """
    Получить тип работы по ID

    - **work_type_id**: ID типа работы
    """
    logger.info("Getting work type by ID", work_type_id=work_type_id)

    service = WorkTypeService(db)
    work_type = service.get_by_id(work_type_id)

    return work_type


@router.post("/", response_model=WorkTypeResponse, status_code=201)
async def create_work_type(
    work_type_data: WorkTypeCreate, db: Session = Depends(get_db)
):
    """
    Создать новый тип работы

    - **name**: название типа работы (обязательно)
    - **description**: описание (опционально)
    - **color**: HEX цвет в формате #RRGGBB (по умолчанию #667eea)
    - **is_active**: активен ли тип работы (по умолчанию true)
    """
    logger.info("Creating work type", name=work_type_data.name)

    service = WorkTypeService(db)
    work_type = service.create(work_type_data)

    logger.info("Work type created", work_type_id=work_type.id)
    return work_type


@router.put("/{work_type_id}", response_model=WorkTypeResponse)
async def update_work_type(
    work_type_id: int, work_type_data: WorkTypeUpdate, db: Session = Depends(get_db)
):
    """
    Обновить тип работы

    - **work_type_id**: ID типа работы
    - Можно обновить любые поля: name, description, color, is_active
    """
    logger.info("Updating work type", work_type_id=work_type_id)

    service = WorkTypeService(db)
    work_type = service.update(work_type_id, work_type_data)

    logger.info("Work type updated", work_type_id=work_type_id)
    return work_type


@router.delete("/{work_type_id}", status_code=204)
async def delete_work_type(
    work_type_id: int,
    soft: bool = Query(False, description="Мягкое удаление (деактивация)"),
    db: Session = Depends(get_db),
):
    """
    Удалить тип работы

    - **work_type_id**: ID типа работы
    - **soft**: если true, то выполняется мягкое удаление (деактивация)

    Нельзя удалить тип работы, который используется в ремонтных работах.
    В таком случае используйте мягкое удаление.
    """
    logger.info("Deleting work type", work_type_id=work_type_id, soft=soft)

    service = WorkTypeService(db)

    if soft:
        service.soft_delete(work_type_id)
        logger.info("Work type soft deleted", work_type_id=work_type_id)
    else:
        service.delete(work_type_id)
        logger.info("Work type deleted", work_type_id=work_type_id)

    return None
