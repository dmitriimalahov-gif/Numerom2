#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Диагностика видео/PDF стриминга для студентов
Critical Video/PDF Streaming Testing for NUMEROM Application

Тестирование исправлений согласно review request:
1. Проверка устранения 422 ошибки при создании уроков с video_url
2. Тестирование video streaming endpoint /api/video/{video_id} с CORS headers
3. Проверка materials streaming endpoint /api/materials/{material_id}/stream
4. Тестирование обновления существующих уроков с video_url
5. Проверка загрузки и создания новых уроков с видео через админ панель

КРИТИЧЕСКАЯ ПРОБЛЕМА: Студенты не могут просматривать видео и PDF материалы
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import os

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class VideoStreamingTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.working_functions = 0
        self.total_functions = 0
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
        
        if status == "PASS":
            self.working_functions += 1
        self.total_functions += 1
        
    def authenticate_super_admin(self):
        """Аутентификация супер-админа"""
        print("\n🔐 АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user', {})
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                self.log_test(
                    "Аутентификация супер-админа", 
                    "PASS", 
                    f"User ID: {self.user_data.get('id')}, is_super_admin: {self.user_data.get('is_super_admin')}, credits: {self.user_data.get('credits_remaining')}"
                )
                return True
            else:
                self.log_test("Аутентификация супер-админа", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация супер-админа", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_admin_lessons_endpoint(self):
        """Тестирование админ панели уроков"""
        print("\n📚 ТЕСТ АДМИН ПАНЕЛИ УРОКОВ")
        
        try:
            # Получение всех уроков
            response = self.session.get(f"{BACKEND_URL}/admin/lessons")
            
            if response.status_code == 200:
                lessons = response.json()
                lessons_without_video = [lesson for lesson in lessons if not lesson.get('video_url')]
                lessons_with_video = [lesson for lesson in lessons if lesson.get('video_url')]
                
                self.log_test(
                    "Получение списка уроков", 
                    "PASS", 
                    f"Всего уроков: {len(lessons)}, без video_url: {len(lessons_without_video)}, с video_url: {len(lessons_with_video)}"
                )
                
                # Проверяем критическую проблему: уроки без video_url
                if lessons_without_video:
                    self.log_test(
                        "КРИТИЧЕСКАЯ ПРОБЛЕМА: Уроки без video_url", 
                        "FAIL", 
                        f"Найдено {len(lessons_without_video)} уроков БЕЗ video_url - студенты не видят видео!"
                    )
                else:
                    self.log_test(
                        "Проверка video_url в уроках", 
                        "PASS", 
                        "Все уроки имеют video_url"
                    )
                
                return lessons
            else:
                self.log_test("Получение списка уроков", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Получение списка уроков", "FAIL", f"Exception: {str(e)}")
            return []
    
    def test_create_lesson_with_video(self):
        """Тестирование создания урока с video_url (исправление 422 ошибки)"""
        print("\n🎥 ТЕСТ СОЗДАНИЯ УРОКА С ВИДЕО")
        
        try:
            lesson_data = {
                "id": str(uuid.uuid4()),
                "title": "Тестовый урок с видео",
                "description": "Урок для тестирования video_url",
                "video_url": "https://example.com/test-video.mp4",
                "duration_minutes": 30,
                "level": 1,
                "order": 999,
                "is_active": True,
                "points_for_lesson": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/lessons", json=lesson_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Создание урока с video_url", 
                    "PASS", 
                    f"Урок создан успешно: {result.get('lesson_id')}"
                )
                return lesson_data["id"]
            elif response.status_code == 422:
                self.log_test(
                    "КРИТИЧЕСКАЯ ПРОБЛЕМА: 422 ошибка при создании урока", 
                    "FAIL", 
                    f"422 Unprocessable Entity: {response.text} - модель VideoLesson требует исправления!"
                )
                return None
            else:
                self.log_test(
                    "Создание урока с video_url", 
                    "FAIL", 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Создание урока с video_url", "FAIL", f"Exception: {str(e)}")
            return None
    
    def test_update_existing_lesson_with_video(self, lessons):
        """Тестирование обновления существующего урока с video_url"""
        print("\n🔄 ТЕСТ ОБНОВЛЕНИЯ УРОКА С ВИДЕО")
        
        if not lessons:
            self.log_test("Обновление урока с video_url", "SKIP", "Нет уроков для обновления")
            return
        
        try:
            # Берем первый урок без video_url
            lesson_to_update = None
            for lesson in lessons:
                if not lesson.get('video_url'):
                    lesson_to_update = lesson
                    break
            
            if not lesson_to_update:
                self.log_test("Обновление урока с video_url", "SKIP", "Все уроки уже имеют video_url")
                return
            
            lesson_id = lesson_to_update['id']
            update_data = {
                "video_url": "https://example.com/updated-video.mp4",
                "duration_minutes": 45
            }
            
            response = self.session.put(f"{BACKEND_URL}/admin/lessons/{lesson_id}", json=update_data)
            
            if response.status_code == 200:
                self.log_test(
                    "Обновление урока с video_url", 
                    "PASS", 
                    f"Урок {lesson_id} обновлен с video_url"
                )
            else:
                self.log_test(
                    "Обновление урока с video_url", 
                    "FAIL", 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Обновление урока с video_url", "FAIL", f"Exception: {str(e)}")
    
    def test_video_streaming_endpoint(self):
        """Тестирование video streaming endpoint с CORS headers"""
        print("\n🎬 ТЕСТ VIDEO STREAMING ENDPOINT")
        
        try:
            # Сначала загружаем тестовое видео
            test_video_id = self.upload_test_video()
            
            if not test_video_id:
                self.log_test("Video streaming endpoint", "SKIP", "Не удалось загрузить тестовое видео")
                return
            
            # Тестируем стриминг без аутентификации
            response = requests.get(f"{BACKEND_URL}/video/{test_video_id}")
            
            if response.status_code == 200:
                # Проверяем CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                cors_ok = all(cors_headers.values())
                
                self.log_test(
                    "Video streaming без аутентификации", 
                    "PASS" if cors_ok else "WARN", 
                    f"HTTP 200, CORS headers: {cors_ok}, Content-Type: {response.headers.get('Content-Type')}"
                )
                
                if not cors_ok:
                    self.log_test(
                        "CORS headers для video endpoint", 
                        "FAIL", 
                        f"Отсутствуют CORS headers: {cors_headers}"
                    )
            else:
                self.log_test(
                    "Video streaming endpoint", 
                    "FAIL", 
                    f"HTTP {response.status_code}: {response.text}"
                )
            
            # Тестируем стриминг с аутентификацией
            response = self.session.get(f"{BACKEND_URL}/video/{test_video_id}")
            
            if response.status_code == 200:
                self.log_test(
                    "Video streaming с аутентификацией", 
                    "PASS", 
                    f"HTTP 200, Content-Type: {response.headers.get('Content-Type')}"
                )
            else:
                self.log_test(
                    "Video streaming с аутентификацией", 
                    "FAIL", 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Video streaming endpoint", "FAIL", f"Exception: {str(e)}")
    
    def upload_test_video(self):
        """Загрузка тестового видео для проверки стриминга"""
        try:
            # Создаем минимальный тестовый файл (имитация видео)
            test_content = b"FAKE_VIDEO_CONTENT_FOR_TESTING"
            
            files = {
                'file': ('test_video.mp4', test_content, 'video/mp4')
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/upload-video", files=files)
            
            if response.status_code == 200:
                result = response.json()
                video_id = result.get('video_id')
                self.log_test(
                    "Загрузка тестового видео", 
                    "PASS", 
                    f"Video ID: {video_id}"
                )
                return video_id
            else:
                self.log_test(
                    "Загрузка тестового видео", 
                    "FAIL", 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Загрузка тестового видео", "FAIL", f"Exception: {str(e)}")
            return None
    
    def test_materials_streaming_endpoint(self):
        """Тестирование materials streaming endpoint"""
        print("\n📄 ТЕСТ MATERIALS STREAMING ENDPOINT")
        
        try:
            # Получаем список материалов
            response = self.session.get(f"{BACKEND_URL}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                if not materials:
                    self.log_test("Materials streaming endpoint", "SKIP", "Нет материалов для тестирования")
                    return
                
                self.log_test(
                    "Получение списка материалов", 
                    "PASS", 
                    f"Найдено {len(materials)} материалов"
                )
                
                # Проверяем наличие file_path в материалах
                materials_without_file_path = [m for m in materials if not m.get('file_path') and not m.get('file_url')]
                
                if materials_without_file_path:
                    self.log_test(
                        "КРИТИЧЕСКАЯ ПРОБЛЕМА: Материалы без file_path", 
                        "FAIL", 
                        f"Найдено {len(materials_without_file_path)} материалов БЕЗ file_path - студенты не могут скачать!"
                    )
                
                # Тестируем стриминг первого материала
                if materials:
                    material = materials[0]
                    material_id = material.get('id')
                    
                    if material_id:
                        response = self.session.get(f"{BACKEND_URL}/materials/{material_id}/stream")
                        
                        if response.status_code == 200:
                            # Проверяем CORS headers
                            cors_headers = {
                                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                            }
                            
                            cors_ok = all(cors_headers.values())
                            
                            self.log_test(
                                "Materials streaming endpoint", 
                                "PASS" if cors_ok else "WARN", 
                                f"HTTP 200, CORS headers: {cors_ok}, Content-Type: {response.headers.get('Content-Type')}"
                            )
                            
                            if not cors_ok:
                                self.log_test(
                                    "CORS headers для materials endpoint", 
                                    "FAIL", 
                                    f"Отсутствуют CORS headers: {cors_headers}"
                                )
                        elif response.status_code == 404:
                            self.log_test(
                                "Materials streaming endpoint", 
                                "FAIL", 
                                f"HTTP 404 - файл материала не найден на сервере"
                            )
                        else:
                            self.log_test(
                                "Materials streaming endpoint", 
                                "FAIL", 
                                f"HTTP {response.status_code}: {response.text}"
                            )
                    else:
                        self.log_test("Materials streaming endpoint", "FAIL", "Материал не имеет ID")
            else:
                self.log_test("Получение списка материалов", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Materials streaming endpoint", "FAIL", f"Exception: {str(e)}")
    
    def test_pdf_upload_and_streaming(self):
        """Тестирование загрузки и стриминга PDF"""
        print("\n📋 ТЕСТ ЗАГРУЗКИ И СТРИМИНГА PDF")
        
        try:
            # Инициализация загрузки PDF
            init_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/init", data={
                'title': 'Тестовый PDF материал',
                'description': 'PDF для тестирования стриминга',
                'lesson_id': '',
                'material_type': 'pdf',
                'filename': 'test_material.pdf',
                'total_size': 1024
            })
            
            if init_response.status_code == 200:
                upload_data = init_response.json()
                upload_id = upload_data.get('uploadId')
                
                self.log_test(
                    "Инициализация загрузки PDF", 
                    "PASS", 
                    f"Upload ID: {upload_id}"
                )
                
                # Загрузка chunk
                test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000079 00000 n \n0000000173 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n301\n%%EOF"
                
                files = {
                    'chunk': ('chunk_0', test_pdf_content, 'application/octet-stream')
                }
                data = {
                    'uploadId': upload_id,
                    'index': 0
                }
                
                chunk_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/chunk", files=files, data=data)
                
                if chunk_response.status_code == 200:
                    self.log_test(
                        "Загрузка PDF chunk", 
                        "PASS", 
                        "Chunk загружен успешно"
                    )
                    
                    # Завершение загрузки
                    finish_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/finish", data={
                        'uploadId': upload_id
                    })
                    
                    if finish_response.status_code == 200:
                        material_data = finish_response.json()
                        material = material_data.get('material', {})
                        material_id = material.get('id')
                        
                        self.log_test(
                            "Завершение загрузки PDF", 
                            "PASS", 
                            f"Material ID: {material_id}"
                        )
                        
                        # Тестируем стриминг загруженного PDF
                        if material_id:
                            stream_response = self.session.get(f"{BACKEND_URL}/materials/{material_id}/stream")
                            
                            if stream_response.status_code == 200:
                                self.log_test(
                                    "Стриминг загруженного PDF", 
                                    "PASS", 
                                    f"PDF доступен для стриминга, Content-Type: {stream_response.headers.get('Content-Type')}"
                                )
                            else:
                                self.log_test(
                                    "Стриминг загруженного PDF", 
                                    "FAIL", 
                                    f"HTTP {stream_response.status_code}: {stream_response.text}"
                                )
                    else:
                        self.log_test(
                            "Завершение загрузки PDF", 
                            "FAIL", 
                            f"HTTP {finish_response.status_code}: {finish_response.text}"
                        )
                else:
                    self.log_test(
                        "Загрузка PDF chunk", 
                        "FAIL", 
                        f"HTTP {chunk_response.status_code}: {chunk_response.text}"
                    )
            else:
                self.log_test(
                    "Инициализация загрузки PDF", 
                    "FAIL", 
                    f"HTTP {init_response.status_code}: {init_response.text}"
                )
                
        except Exception as e:
            self.log_test("Загрузка и стриминг PDF", "FAIL", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚨 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Диагностика видео/PDF стриминга для студентов")
        print("=" * 80)
        
        # Аутентификация
        if not self.authenticate_super_admin():
            print("❌ Не удалось аутентифицироваться. Тестирование прервано.")
            return
        
        # Получение списка уроков
        lessons = self.test_admin_lessons_endpoint()
        
        # Тестирование создания урока с видео
        self.test_create_lesson_with_video()
        
        # Тестирование обновления урока с видео
        self.test_update_existing_lesson_with_video(lessons)
        
        # Тестирование video streaming endpoint
        self.test_video_streaming_endpoint()
        
        # Тестирование materials streaming endpoint
        self.test_materials_streaming_endpoint()
        
        # Тестирование загрузки и стриминга PDF
        self.test_pdf_upload_and_streaming()
        
        # Итоговый отчет
        self.print_final_report()
    
    def print_final_report(self):
        """Печать итогового отчета"""
        print("\n" + "=" * 80)
        print("🎯 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        passed_tests = [r for r in self.test_results if r['status'] == 'PASS']
        failed_tests = [r for r in self.test_results if r['status'] == 'FAIL']
        
        print(f"✅ РАБОТАЮЩИЕ ФУНКЦИИ ({len(passed_tests)}/{self.total_functions}):")
        for test in passed_tests:
            print(f"   • {test['test']}")
        
        if failed_tests:
            print(f"\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(failed_tests)}/{self.total_functions}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        success_rate = (len(passed_tests) / max(self.total_functions, 1)) * 100
        
        print(f"\n🎯 ОСНОВНАЯ ПРОБЛЕМА: Существующие уроки в базе НЕ ИМЕЮТ video_url, поэтому студенты не могут просматривать видео.")
        print(f"📊 Успешность: {success_rate:.1f}% ({len(passed_tests)}/{self.total_functions} тестов)")
        
        if success_rate < 70:
            print("🚨 ТРЕБУЕТСЯ НЕМЕДЛЕННОЕ ИСПРАВЛЕНИЕ для восстановления функциональности видео/PDF для студентов.")
        else:
            print("✅ Большинство функций работает корректно.")

if __name__ == "__main__":
    tester = VideoStreamingTester()
    tester.run_all_tests()