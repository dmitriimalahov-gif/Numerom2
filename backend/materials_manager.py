"""
Система управления учебными материалами для суперадминистратора
"""
import os
import uuid
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, UploadFile
from pathlib import Path

# Директория для хранения файлов
MATERIALS_DIR = Path("/app/materials")
MATERIALS_DIR.mkdir(exist_ok=True)

class MaterialsManager:
    """Менеджер для работы с учебными материалами"""
    
    def __init__(self, db):
        self.db = db
        
    async def upload_pdf_material(self, lesson_id: str, title: str, description: str, 
                                 file_content: bytes, file_name: str, uploaded_by: str) -> Dict[str, Any]:
        """Загрузка PDF материала"""
        
        # Создаем уникальное имя файла
        file_extension = Path(file_name).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = MATERIALS_DIR / unique_filename
        
        # Сохраняем файл на диск
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Создаем запись в базе данных
        material_data = {
            "id": str(uuid.uuid4()),
            "lesson_id": lesson_id,
            "title": title,
            "description": description,
            "material_type": "pdf",
            "file_name": file_name,
            "stored_file_name": unique_filename,
            "file_size": len(file_content),
            "file_path": str(file_path),
            "file_url": f"/api/materials/file/{unique_filename}",
            "uploaded_by": uploaded_by,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        await self.db.lesson_materials.insert_one(material_data)
        
        return material_data
    
    async def upload_video_material(self, lesson_id: str, title: str, description: str,
                                   video_url: str, uploaded_by: str) -> Dict[str, Any]:
        """Добавление видео материала"""
        
        material_data = {
            "id": str(uuid.uuid4()),
            "lesson_id": lesson_id,
            "title": title,
            "description": description,
            "material_type": "video",
            "video_url": video_url,
            "uploaded_by": uploaded_by,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        await self.db.lesson_materials.insert_one(material_data)
        
        return material_data
    
    async def get_lesson_materials(self, lesson_id: str) -> List[Dict[str, Any]]:
        """Получение всех материалов для урока"""
        
        materials = await self.db.lesson_materials.find({
            "lesson_id": lesson_id,
            "is_active": True
        }).to_list(100)
        
        return materials
    
    async def get_material_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Получение материала по имени файла"""
        
        material = await self.db.lesson_materials.find_one({
            "stored_file_name": filename,
            "is_active": True
        })
        
        return material
    
    async def delete_material(self, material_id: str, deleted_by: str) -> bool:
        """Удаление материала"""
        
        # Помечаем как удаленный
        result = await self.db.lesson_materials.update_one(
            {"id": material_id},
            {"$set": {
                "is_active": False,
                "deleted_by": deleted_by,
                "deleted_at": datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0
    
    async def create_enhanced_lesson(self, lesson_data: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        """Создание улучшенного урока с материалами"""
        
        lesson = {
            "id": str(uuid.uuid4()),
            "module_name": lesson_data["module_name"],
            "lesson_number": lesson_data["lesson_number"],
            "title": lesson_data["title"],
            "content_description": lesson_data["content_description"],
            "learning_objectives": lesson_data.get("learning_objectives", []),
            "assignments": lesson_data.get("assignments", []),
            "social_mechanics": lesson_data.get("social_mechanics", []),
            "additional_materials": lesson_data.get("additional_materials", []),
            "expected_results": lesson_data.get("expected_results", []),
            "duration_minutes": lesson_data.get("duration_minutes", 45),
            "difficulty_level": lesson_data.get("difficulty_level", 1),
            "prerequisites": lesson_data.get("prerequisites", []),
            "materials": [],  # Будет заполнено позже
            "video_url": lesson_data.get("video_url"),
            "quiz": lesson_data.get("quiz"),
            "is_active": True,
            "created_by": created_by,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await self.db.enhanced_lessons.insert_one(lesson)
        
        return lesson
    
    async def update_lesson(self, lesson_id: str, updates: Dict[str, Any], updated_by: str) -> bool:
        """Обновление урока"""
        
        updates["updated_at"] = datetime.utcnow()
        updates["updated_by"] = updated_by
        
        result = await self.db.enhanced_lessons.update_one(
            {"id": lesson_id},
            {"$set": updates}
        )
        
        return result.modified_count > 0
    
    async def get_all_lessons(self) -> List[Dict[str, Any]]:
        """Получение всех активных уроков"""
        
        lessons = await self.db.enhanced_lessons.find({
            "is_active": True
        }).sort("lesson_number", 1).to_list(100)
        
        # Добавляем материалы к каждому уроку
        for lesson in lessons:
            lesson["materials"] = await self.get_lesson_materials(lesson["id"])
        
        return lessons
    
    async def get_lesson_by_id(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """Получение урока по ID"""
        
        lesson = await self.db.enhanced_lessons.find_one({
            "id": lesson_id,
            "is_active": True
        })
        
        if lesson:
            lesson["materials"] = await self.get_lesson_materials(lesson_id)
        
        return lesson
    
    async def log_admin_action(self, action_type: str, target_id: str, 
                              details: Dict[str, Any], performed_by: str):
        """Логирование действий суперадминистратора"""
        
        log_entry = {
            "id": str(uuid.uuid4()),
            "action_type": action_type,
            "target_id": target_id,
            "details": details,
            "performed_by": performed_by,
            "performed_at": datetime.utcnow()
        }
        
        await self.db.admin_actions.insert_one(log_entry)
    
    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Получение прогресса пользователя"""
        
        progress = await self.db.user_progress.find_one({"user_id": user_id})
        
        if not progress:
            # Создаем новую запись прогресса
            progress = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "completed_lessons": [],
                "quiz_results": {},
                "total_score": 0,
                "level": 1,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await self.db.user_progress.insert_one(progress)
        
        return progress
    
    async def update_user_progress(self, user_id: str, lesson_id: str, quiz_score: int = None):
        """Обновление прогресса пользователя"""
        
        progress = await self.get_user_progress(user_id)
        
        updates = {
            "updated_at": datetime.utcnow()
        }
        
        # Добавляем урок в завершенные, если его там нет
        if lesson_id not in progress.get("completed_lessons", []):
            updates["$addToSet"] = {"completed_lessons": lesson_id}
        
        # Обновляем результат квиза
        if quiz_score is not None:
            updates[f"quiz_results.{lesson_id}"] = quiz_score
            
            # Пересчитываем общий балл
            total_score = sum(progress.get("quiz_results", {}).values()) + quiz_score
            updates["total_score"] = total_score
            
            # Определяем уровень на основе количества завершенных уроков
            completed_count = len(progress.get("completed_lessons", [])) + 1
            updates["level"] = min(completed_count // 2 + 1, 10)  # Максимум 10 уровней
        
        await self.db.user_progress.update_one(
            {"user_id": user_id},
            {"$set": updates}
        )

# Глобальный менеджер материалов
materials_manager = None

def get_materials_manager(db):
    """Получение экземпляра менеджера материалов"""
    global materials_manager
    if materials_manager is None:
        materials_manager = MaterialsManager(db)
    return materials_manager