"""
Сервис для работы с типами работ
"""

import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import WorkType
from ..schemas.work_type import WorkTypeCreate, WorkTypeUpdate
from ..utils.exceptions import (
    BusinessLogicError,
    DuplicateEntityError,
    EntityNotFoundError,
)

logger = structlog.get_logger(__name__)


class WorkTypeService:
    """Сервис для работы с типами работ"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, include_inactive: bool = False) -> list[WorkType]:
        """
        Получить все типы работ

        Args:
            include_inactive: Включать ли неактивные типы

        Returns:
            Список типов работ
        """
        logger.info("Getting all work types", include_inactive=include_inactive)

        query = self.db.query(WorkType)
        if not include_inactive:
            query = query.filter(WorkType.is_active)

        work_types = query.order_by(WorkType.name).all()

        logger.info("Retrieved work types", count=len(work_types))
        return work_types

    def get_by_id(self, work_type_id: int) -> WorkType:
        """
        Получить тип работы по ID

        Args:
            work_type_id: ID типа работы

        Returns:
            Тип работы

        Raises:
            EntityNotFoundError: Если тип работы не найден
        """
        logger.info("Getting work type by ID", work_type_id=work_type_id)

        work_type = self.db.query(WorkType).filter(WorkType.id == work_type_id).first()

        if not work_type:
            logger.warning("Work type not found", work_type_id=work_type_id)
            raise EntityNotFoundError(f"Тип работы с ID {work_type_id} не найден")

        logger.info(
            "Retrieved work type", work_type_id=work_type_id, name=work_type.name
        )
        return work_type

    def create(self, work_type_data: WorkTypeCreate) -> WorkType:
        """
        Создать новый тип работы

        Args:
            work_type_data: Данные для создания

        Returns:
            Созданный тип работы

        Raises:
            DuplicateEntityError: Если тип работы с таким именем уже существует
        """
        logger.info("Creating work type", name=work_type_data.name)

        # Проверяем уникальность имени
        existing = (
            self.db.query(WorkType).filter(WorkType.name == work_type_data.name).first()
        )
        if existing:
            logger.warning(
                "Work type with this name already exists", name=work_type_data.name
            )
            raise DuplicateEntityError(
                f"Тип работы с именем '{work_type_data.name}' уже существует"
            )

        # Создаем новый тип работы
        work_type = WorkType(
            name=work_type_data.name,
            description=work_type_data.description,
            color=work_type_data.color,
            is_active=work_type_data.is_active,
        )

        try:
            self.db.add(work_type)
            self.db.commit()
            self.db.refresh(work_type)

            logger.info(
                "Work type created successfully",
                work_type_id=work_type.id,
                name=work_type.name,
            )
            return work_type

        except IntegrityError as e:
            self.db.rollback()
            logger.error("Database integrity error creating work type", error=str(e))
            raise DuplicateEntityError(
                f"Тип работы с именем '{work_type_data.name}' уже существует"
            ) from e

    def update(self, work_type_id: int, work_type_data: WorkTypeUpdate) -> WorkType:
        """
        Обновить тип работы

        Args:
            work_type_id: ID типа работы
            work_type_data: Данные для обновления

        Returns:
            Обновленный тип работы

        Raises:
            EntityNotFoundError: Если тип работы не найден
            DuplicateEntityError: Если новое имя уже существует
        """
        logger.info("Updating work type", work_type_id=work_type_id)

        # Получаем тип работы
        work_type = self.get_by_id(work_type_id)

        # Проверяем уникальность имени, если оно изменяется
        if work_type_data.name and work_type_data.name != work_type.name:
            existing = (
                self.db.query(WorkType)
                .filter(
                    WorkType.name == work_type_data.name, WorkType.id != work_type_id
                )
                .first()
            )
            if existing:
                logger.warning(
                    "Work type with this name already exists", name=work_type_data.name
                )
                raise DuplicateEntityError(
                    f"Тип работы с именем '{work_type_data.name}' уже существует"
                )

        # Обновляем поля
        update_data = work_type_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(work_type, field, value)

        try:
            self.db.commit()
            self.db.refresh(work_type)

            logger.info(
                "Work type updated successfully",
                work_type_id=work_type_id,
                name=work_type.name,
            )
            return work_type

        except IntegrityError as e:
            self.db.rollback()
            logger.error("Database integrity error updating work type", error=str(e))
            raise DuplicateEntityError(
                "Ошибка обновления: нарушение уникальности"
            ) from e

    def delete(self, work_type_id: int) -> None:
        """
        Удалить тип работы

        Args:
            work_type_id: ID типа работы

        Raises:
            EntityNotFoundError: Если тип работы не найден
            BusinessLogicError: Если тип работы используется в ремонтных работах
        """
        logger.info("Deleting work type", work_type_id=work_type_id)

        # Получаем тип работы
        work_type = self.get_by_id(work_type_id)

        # Проверяем, используется ли тип работы
        if len(work_type.repair_works) > 0:
            logger.warning(
                "Cannot delete work type with associated repair works",
                work_type_id=work_type_id,
                repair_works_count=len(work_type.repair_works),
            )
            raise BusinessLogicError(
                f"Нельзя удалить тип работы, используемый в {len(work_type.repair_works)} ремонтных работах"
            )

        try:
            self.db.delete(work_type)
            self.db.commit()

            logger.info("Work type deleted successfully", work_type_id=work_type_id)

        except Exception as e:
            self.db.rollback()
            logger.error("Error deleting work type", error=str(e))
            raise BusinessLogicError(
                f"Ошибка при удалении типа работы: {str(e)}"
            ) from e

    def soft_delete(self, work_type_id: int) -> WorkType:
        """
        Мягкое удаление типа работы (деактивация)

        Args:
            work_type_id: ID типа работы

        Returns:
            Деактивированный тип работы
        """
        logger.info("Soft deleting work type", work_type_id=work_type_id)

        work_type = self.get_by_id(work_type_id)
        work_type.is_active = False

        self.db.commit()
        self.db.refresh(work_type)

        logger.info("Work type soft deleted successfully", work_type_id=work_type_id)
        return work_type
