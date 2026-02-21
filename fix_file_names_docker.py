#!/usr/bin/env python3
"""
Скрипт для исправления stored_name в базе данных файлов,
запускается внутри Docker контейнера backend.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path

async def fix_file_names():
    """Исправляет stored_name в базе данных файлов"""

    # Подключение к MongoDB внутри Docker сети
    client = AsyncIOMotorClient("mongodb://mongodb:27017")
    db = client.numerom

    # Папка с файлами внутри контейнера
    uploads_dir = Path("/app/uploads/learning_v2")

    print("🔍 Ищу файлы в базе данных...")

    try:
        # Получаем все файлы из базы данных
        files_cursor = db.files.find({})
        files = await files_cursor.to_list(length=None)

        print(f"📁 Найдено {len(files)} файлов в базе данных")

        for file_doc in files:
            file_id = file_doc.get('id')
            original_name = file_doc.get('original_name')
            current_stored_name = file_doc.get('stored_name')

            print(f"\n📄 Обрабатываю файл: {original_name}")
            print(f"   ID: {file_id}")
            print(f"   Текущий stored_name: {current_stored_name}")

            # Ищем реальный файл в папке uploads
            real_file_path = None

            # Сначала ищем файл с current_stored_name
            potential_path = uploads_dir / current_stored_name
            if potential_path.exists():
                real_file_path = potential_path
                print(f"   ✅ Файл найден по stored_name: {current_stored_name}")
            else:
                # Ищем файл по original_name
                potential_path = uploads_dir / original_name
                if potential_path.exists():
                    real_file_path = potential_path
                    print(f"   🔄 Файл найден по original_name: {original_name}")
                else:
                    # Ищем файл с похожим именем (без UUID)
                    for file_path in uploads_dir.glob("*"):
                        if file_path.is_file() and file_path.suffix and original_name in file_path.name:
                            real_file_path = file_path
                            print(f"   🔍 Файл найден по частичному совпадению: {file_path.name}")
                            break

            if real_file_path:
                new_stored_name = real_file_path.name

                # Обновляем stored_name и file_path в базе данных
                update_result = await db.files.update_one(
                    {"id": file_id},
                    {
                        "$set": {
                            "stored_name": new_stored_name,
                            "file_path": str(real_file_path)
                        }
                    }
                )

                if update_result.modified_count > 0:
                    print(f"   ✅ Обновлено: stored_name = {new_stored_name}")
                else:
                    print(f"   ⚠️  Не удалось обновить")
            else:
                print(f"   ❌ Файл не найден на диске: {original_name}")

        print("\n🎉 Исправление завершено!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_file_names())



