"""
Сервис для работы с ремонтными работами
"""

from datetime import datetime

import structlog
from sqlalchemy.orm import Session

from ..models import RepairWork
from ..schemas.repair_work import RepairWorkCreate, RepairWorkUpdate, WorkStatus

logger = structlog.get_logger(__name__)


class RepairWorkService:
    """Сервис для работы с ремонтными работами"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        status: WorkStatus | None = None,
        work_type_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        is_completed: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RepairWork]:
        """
        Получить все ремонтные работы с фильтрами
        """
        logger.info(
            "Getting repair works",
            status=status,
            work_type_id=work_type_id,
            start_date=start_date,
            end_date=end_date,
            is_completed=is_completed,
        )

        query = self.db.query(RepairWork)

        # Фильтр по статусу
        if status:
            query = query.filter(RepairWork.status == status)

        # Фильтр по типу работы
        if work_type_id:
            query = query.filter(RepairWork.work_type_id == work_type_id)

        # Фильтр по дате начала
        if start_date:
            query = query.filter(RepairWork.start_datetime >= start_date)

        # Фильтр по дате окончания
        if end_date:
            query = query.filter(RepairWork.start_datetime <= end_date)

        # Фильтр по завершенности работ
        if is_completed is not None:
            if is_completed:
                # Завершенные работы - статус COMPLETED
                query = query.filter(RepairWork.status == WorkStatus.COMPLETED)
            else:
                # Незавершенные работы - все статусы кроме COMPLETED
                query = query.filter(RepairWork.status != WorkStatus.COMPLETED)

        # Сортировка по дате создания (новые сначала)
        query = query.order_by(RepairWork.created_at.desc())

        repair_works = query.offset(offset).limit(limit).all()
        logger.info("Found repair works", count=len(repair_works))
        return repair_works

    def get_by_id(self, repair_work_id: int) -> RepairWork | None:
        """
        Получить ремонтную работу по ID
        """
        logger.info("Getting repair work by ID", repair_work_id=repair_work_id)
        repair_work = (
            self.db.query(RepairWork).filter(RepairWork.id == repair_work_id).first()
        )
        if repair_work:
            logger.info("Found repair work", repair_work_id=repair_work_id)
        else:
            logger.warning("Repair work not found", repair_work_id=repair_work_id)
        return repair_work

    def create(self, repair_work_data: RepairWorkCreate) -> RepairWork:
        """
        Создать новую ремонтную работу
        """
        logger.info("Creating repair work", data=repair_work_data.model_dump())

        # Создаем новую ремонтную работу
        repair_work = RepairWork(
            location=repair_work_data.location,
            start_location=repair_work_data.start_location,
            end_location=repair_work_data.end_location,
            latitude=repair_work_data.latitude,
            longitude=repair_work_data.longitude,
            start_latitude=repair_work_data.start_latitude,
            start_longitude=repair_work_data.start_longitude,
            end_latitude=repair_work_data.end_latitude,
            end_longitude=repair_work_data.end_longitude,
            description=repair_work_data.description,
            notes=repair_work_data.notes,
            start_datetime=repair_work_data.start_datetime,
            end_datetime=repair_work_data.end_datetime,
            planned_duration_hours=repair_work_data.planned_duration_hours,
            work_type_id=repair_work_data.work_type_id,
            status=repair_work_data.status or WorkStatus.PLANNED,
            # Поля сегмента улицы
            street_segment_geojson=repair_work_data.street_segment_geojson,
            street_name=repair_work_data.street_name,
            street_osm_type=repair_work_data.street_osm_type,
            street_osm_id=repair_work_data.street_osm_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.db.add(repair_work)
        self.db.commit()
        self.db.refresh(repair_work)

        logger.info("Repair work created", repair_work_id=repair_work.id)
        return repair_work

    def update(
        self, repair_work_id: int, repair_work_data: RepairWorkUpdate
    ) -> RepairWork | None:
        """
        Обновить ремонтную работу
        """
        logger.info("Updating repair work", repair_work_id=repair_work_id)

        repair_work = self.get_by_id(repair_work_id)
        if not repair_work:
            return None

        # Обновляем только переданные поля
        update_data = repair_work_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(repair_work, field):
                setattr(repair_work, field, value)

        repair_work.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(repair_work)

        logger.info("Repair work updated", repair_work_id=repair_work_id)
        return repair_work

    def delete(self, repair_work_id: int) -> bool:
        """
        Удалить ремонтную работу
        """
        logger.info("Deleting repair work", repair_work_id=repair_work_id)

        repair_work = self.get_by_id(repair_work_id)
        if not repair_work:
            return False

        self.db.delete(repair_work)
        self.db.commit()

        logger.info("Repair work deleted", repair_work_id=repair_work_id)
        return True
