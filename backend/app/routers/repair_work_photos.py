"""
API endpoints для фотографий ремонтных работ
"""

import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.repair_work_photo import RepairWorkPhoto
from ..schemas.repair_work_photo import (
    RepairWorkPhoto as RepairWorkPhotoSchema,
    RepairWorkPhotoCreate,
    RepairWorkPhotoList,
    RepairWorkPhotoUpdate,
)
from ..services.repair_work_service import RepairWorkService

router = APIRouter(prefix="/api/v1/repair-works", tags=["repair-work-photos"])

# Настройки для загрузки файлов
UPLOAD_DIR = "uploads/repair_work_photos"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Создаем папку для загрузок если её нет
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_image_file(file: UploadFile) -> None:
    """Валидация загружаемого файла"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не указано имя файла"
        )
    
    # Проверяем расширение
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Проверяем MIME тип
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть изображением"
        )


@router.get("/{work_id}/photos", response_model=RepairWorkPhotoList)
async def get_repair_work_photos(
    work_id: int,
    db: Session = Depends(get_db)
) -> RepairWorkPhotoList:
    """Получить все фотографии ремонтной работы"""
    
    # Проверяем существование работы
    work_service = RepairWorkService(db)
    work = work_service.get_repair_work(work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ремонтная работа не найдена"
        )
    
    # Получаем фотографии
    photos = db.query(RepairWorkPhoto).filter(
        RepairWorkPhoto.repair_work_id == work_id
    ).order_by(RepairWorkPhoto.sort_order, RepairWorkPhoto.created_at).all()
    
    return RepairWorkPhotoList(photos=photos, total=len(photos))


@router.post("/{work_id}/photos", response_model=RepairWorkPhotoSchema)
async def upload_repair_work_photo(
    work_id: int,
    file: UploadFile = File(...),
    description: str = Form(None),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
) -> RepairWorkPhotoSchema:
    """Загрузить фотографию для ремонтной работы"""
    
    # Проверяем существование работы
    work_service = RepairWorkService(db)
    work = work_service.get_repair_work(work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ремонтная работа не найдена"
        )
    
    # Валидируем файл
    validate_image_file(file)
    
    # Читаем содержимое файла
    file_content = await file.read()
    file_size = len(file_content)
    
    # Проверяем размер
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Генерируем уникальное имя файла
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Сохраняем файл
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сохранения файла: {str(e)}"
        )
    
    # Создаем запись в базе данных
    photo_data = RepairWorkPhotoCreate(
        repair_work_id=work_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        description=description,
        sort_order=sort_order
    )
    
    photo = RepairWorkPhoto(**photo_data.model_dump())
    db.add(photo)
    db.commit()
    db.refresh(photo)
    
    return photo


@router.put("/{work_id}/photos/{photo_id}", response_model=RepairWorkPhotoSchema)
async def update_repair_work_photo(
    work_id: int,
    photo_id: int,
    photo_update: RepairWorkPhotoUpdate,
    db: Session = Depends(get_db)
) -> RepairWorkPhotoSchema:
    """Обновить информацию о фотографии"""
    
    # Проверяем существование фотографии
    photo = db.query(RepairWorkPhoto).filter(
        RepairWorkPhoto.id == photo_id,
        RepairWorkPhoto.repair_work_id == work_id
    ).first()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена"
        )
    
    # Обновляем данные
    update_data = photo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(photo, field, value)
    
    db.commit()
    db.refresh(photo)
    
    return photo


@router.delete("/{work_id}/photos/{photo_id}")
async def delete_repair_work_photo(
    work_id: int,
    photo_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Удалить фотографию"""
    
    # Проверяем существование фотографии
    photo = db.query(RepairWorkPhoto).filter(
        RepairWorkPhoto.id == photo_id,
        RepairWorkPhoto.repair_work_id == work_id
    ).first()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена"
        )
    
    # Удаляем файл с диска
    try:
        if os.path.exists(photo.file_path):
            os.remove(photo.file_path)
    except Exception as e:
        # Логируем ошибку, но не прерываем операцию
        print(f"Ошибка удаления файла {photo.file_path}: {e}")
    
    # Удаляем запись из базы данных
    db.delete(photo)
    db.commit()
    
    return {"message": "Фотография удалена"}


@router.get("/{work_id}/photos/{photo_id}/download")
async def download_repair_work_photo(
    work_id: int,
    photo_id: int,
    db: Session = Depends(get_db)
):
    """Скачать файл фотографии"""
    
    # Проверяем существование фотографии
    photo = db.query(RepairWorkPhoto).filter(
        RepairWorkPhoto.id == photo_id,
        RepairWorkPhoto.repair_work_id == work_id
    ).first()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена"
        )
    
    # Проверяем существование файла
    if not os.path.exists(photo.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл фотографии не найден"
        )
    
    from fastapi.responses import FileResponse
    
    return FileResponse(
        path=photo.file_path,
        filename=photo.filename,
        media_type=photo.mime_type
    ) 