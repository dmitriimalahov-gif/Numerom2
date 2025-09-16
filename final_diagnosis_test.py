#!/usr/bin/env python3
"""
ФИНАЛЬНАЯ ДИАГНОСТИКА: Полный анализ проблем с видео/PDF для студентов
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
TEST_ADMIN_PASSWORD = "756bvy67H"

class FinalDiagnosisTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.student_token = None
        self.issues_found = []
        self.working_features = []
        
    def log_issue(self, issue):
        self.issues_found.append(issue)
        print(f"❌ ПРОБЛЕМА: {issue}")
    
    def log_working(self, feature):
        self.working_features.append(feature)
        print(f"✅ РАБОТАЕТ: {feature}")
    
    def authenticate_users(self):
        """Authenticate admin and create student with credits"""
        print("🔐 АУТЕНТИФИКАЦИЯ ПОЛЬЗОВАТЕЛЕЙ")
        
        # Admin auth
        try:
            login_data = {"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD}
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                print(f"✅ Админ аутентифицирован: {data.get('user', {}).get('id')}")
            else:
                self.log_issue("Не удалось аутентифицировать администратора")
                return False
        except Exception as e:
            self.log_issue(f"Ошибка аутентификации админа: {str(e)}")
            return False
        
        # Create student with more credits
        try:
            student_data = {
                "email": "rich.student@example.com",
                "password": "testpass123",
                "full_name": "Rich Student",
                "birth_date": "15.03.1990",
                "city": "Москва",
                "phone_number": "+7900123456"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=student_data)
            
            if response.status_code == 200:
                data = response.json()
                self.student_token = data.get('access_token')
                student_id = data.get('user', {}).get('id')
                print(f"✅ Студент создан: {student_id}")
                
                # Give student more credits via admin
                admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
                credit_data = {'credits_remaining': 100}
                
                credit_response = self.session.patch(
                    f"{BACKEND_URL}/admin/users/{student_id}/credits", 
                    json=credit_data, 
                    headers=admin_headers
                )
                
                if credit_response.status_code == 200:
                    print(f"✅ Студенту добавлено 100 кредитов")
                else:
                    print(f"⚠️ Не удалось добавить кредиты: {credit_response.status_code}")
                
                return True
            else:
                self.log_issue(f"Не удалось создать студента: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_issue(f"Ошибка создания студента: {str(e)}")
            return False
    
    def diagnose_video_streaming(self):
        """Диагностика стриминга видео"""
        print("\n🎥 ДИАГНОСТИКА СТРИМИНГА ВИДЕО")
        
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        student_headers = {'Authorization': f'Bearer {self.student_token}'}
        
        # 1. Check if video upload works
        try:
            test_video_content = b"FAKE_VIDEO_CONTENT" * 200
            files = {'file': ('test_video.mp4', test_video_content, 'video/mp4')}
            
            response = self.session.post(f"{BACKEND_URL}/admin/upload-video", files=files, headers=admin_headers)
            
            if response.status_code == 200:
                video_data = response.json()
                video_id = video_data.get('video_id')
                self.log_working("Загрузка видео администратором")
                
                # 2. Test video streaming without auth
                stream_response = self.session.get(f"{BACKEND_URL}/video/{video_id}")
                
                if stream_response.status_code == 200:
                    content_type = stream_response.headers.get('content-type', '')
                    if 'video/' in content_type:
                        self.log_working("Стриминг видео без аутентификации")
                    else:
                        self.log_issue(f"Неверный Content-Type для видео: {content_type}")
                else:
                    self.log_issue(f"Стриминг видео не работает: {stream_response.status_code}")
                
                # 3. Test video streaming with student auth
                stream_response = self.session.get(f"{BACKEND_URL}/video/{video_id}", headers=student_headers)
                
                if stream_response.status_code == 200:
                    self.log_working("Стриминг видео с аутентификацией студента")
                else:
                    self.log_issue(f"Стриминг видео с аутентификацией не работает: {stream_response.status_code}")
                
                # 4. Create lesson with this video
                lesson_data = {
                    "id": "test-lesson-with-video",
                    "title": "Test Lesson with Video",
                    "description": "Test lesson for video streaming",
                    "video_url": f"/api/video/{video_id}",
                    "level": 1,
                    "order": 1,
                    "is_active": True,
                    "points_for_lesson": 5  # Lower cost for testing
                }
                
                lesson_response = self.session.post(f"{BACKEND_URL}/admin/lessons", json=lesson_data, headers=admin_headers)
                
                if lesson_response.status_code == 200:
                    self.log_working("Создание урока с видео")
                    
                    # 5. Test lesson start by student
                    start_response = self.session.post(f"{BACKEND_URL}/learning/lesson/test-lesson-with-video/start", headers=student_headers)
                    
                    if start_response.status_code == 200:
                        self.log_working("Начало урока с видео студентом")
                    else:
                        self.log_issue(f"Студент не может начать урок с видео: {start_response.status_code} - {start_response.text}")
                else:
                    self.log_issue(f"Не удалось создать урок с видео: {lesson_response.status_code}")
                    
            else:
                self.log_issue(f"Загрузка видео не работает: {response.status_code}")
                
        except Exception as e:
            self.log_issue(f"Ошибка диагностики видео: {str(e)}")
    
    def diagnose_pdf_streaming(self):
        """Диагностика стриминга PDF"""
        print("\n📄 ДИАГНОСТИКА СТРИМИНГА PDF")
        
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        student_headers = {'Authorization': f'Bearer {self.student_token}'}
        
        # Create a proper PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
        
        try:
            # 1. Initialize PDF upload
            init_data = {
                'title': 'Test PDF Material for Streaming',
                'description': 'Test PDF to check streaming functionality',
                'lesson_id': '',
                'material_type': 'pdf',
                'filename': 'test_streaming.pdf',
                'total_size': len(pdf_content)
            }
            
            init_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/init", data=init_data, headers=admin_headers)
            
            if init_response.status_code == 200:
                upload_data = init_response.json()
                upload_id = upload_data.get('uploadId')
                self.log_working("Инициализация загрузки PDF")
                
                # 2. Upload PDF chunk
                chunk_data = {'uploadId': upload_id, 'index': 0}
                files = {'chunk': ('chunk_0', pdf_content, 'application/octet-stream')}
                
                chunk_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/chunk", data=chunk_data, files=files, headers=admin_headers)
                
                if chunk_response.status_code == 200:
                    self.log_working("Загрузка chunk PDF")
                    
                    # 3. Finish PDF upload
                    finish_data = {'uploadId': upload_id}
                    finish_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/finish", data=finish_data, headers=admin_headers)
                    
                    if finish_response.status_code == 200:
                        material_data = finish_response.json()
                        material = material_data.get('material', {})
                        material_id = material.get('id')
                        self.log_working("Завершение загрузки PDF")
                        
                        # 4. Test PDF streaming by student
                        stream_response = self.session.get(f"{BACKEND_URL}/materials/{material_id}/stream", headers=student_headers)
                        
                        if stream_response.status_code == 200:
                            content_type = stream_response.headers.get('content-type', '')
                            if 'application/pdf' in content_type:
                                self.log_working("Стриминг PDF студентом")
                            else:
                                self.log_issue(f"Неверный Content-Type для PDF: {content_type}")
                        elif stream_response.status_code == 402:
                            self.log_issue("Студент не может просматривать PDF - недостаточно кредитов")
                        else:
                            self.log_issue(f"Стриминг PDF не работает: {stream_response.status_code} - {stream_response.text}")
                        
                        # 5. Test PDF streaming without auth
                        stream_response_no_auth = self.session.get(f"{BACKEND_URL}/materials/{material_id}/stream")
                        
                        if stream_response_no_auth.status_code == 401:
                            self.log_working("PDF защищен аутентификацией")
                        else:
                            self.log_issue(f"PDF не защищен аутентификацией: {stream_response_no_auth.status_code}")
                            
                    else:
                        self.log_issue(f"Не удалось завершить загрузку PDF: {finish_response.status_code} - {finish_response.text}")
                else:
                    self.log_issue(f"Не удалось загрузить chunk PDF: {chunk_response.status_code}")
            else:
                self.log_issue(f"Не удалось инициализировать загрузку PDF: {init_response.status_code}")
                
        except Exception as e:
            self.log_issue(f"Ошибка диагностики PDF: {str(e)}")
    
    def check_existing_content_issues(self):
        """Проверка проблем с существующим контентом"""
        print("\n🔍 ПРОВЕРКА СУЩЕСТВУЮЩЕГО КОНТЕНТА")
        
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        student_headers = {'Authorization': f'Bearer {self.student_token}'}
        
        # Check existing lessons
        try:
            lessons_response = self.session.get(f"{BACKEND_URL}/learning/levels", headers=student_headers)
            
            if lessons_response.status_code == 200:
                data = lessons_response.json()
                lessons = data.get('available_lessons', [])
                
                video_lessons = [l for l in lessons if l.get('video_url')]
                empty_video_lessons = [l for l in lessons if not l.get('video_url')]
                
                if empty_video_lessons:
                    self.log_issue(f"Найдено {len(empty_video_lessons)} уроков без видео URL")
                
                if video_lessons:
                    self.log_working(f"Найдено {len(video_lessons)} уроков с видео URL")
                else:
                    self.log_issue("Нет уроков с видео URL в системе")
                    
        except Exception as e:
            self.log_issue(f"Ошибка проверки уроков: {str(e)}")
        
        # Check existing materials
        try:
            materials_response = self.session.get(f"{BACKEND_URL}/materials", headers=student_headers)
            
            if materials_response.status_code == 200:
                materials = materials_response.json()
                
                pdf_materials = [m for m in materials if m.get('material_type') == 'pdf']
                materials_with_paths = [m for m in materials if m.get('file_path')]
                
                if not pdf_materials:
                    self.log_issue("Нет PDF материалов в системе")
                else:
                    self.log_working(f"Найдено {len(pdf_materials)} PDF материалов")
                
                if not materials_with_paths:
                    self.log_issue("Материалы не имеют file_path")
                    
                # Try to access first material
                if materials:
                    first_material = materials[0]
                    material_id = first_material.get('id')
                    
                    access_response = self.session.get(f"{BACKEND_URL}/materials/{material_id}/stream", headers=student_headers)
                    
                    if access_response.status_code == 404:
                        self.log_issue(f"Материал {material_id} не найден на диске (404)")
                    elif access_response.status_code == 200:
                        self.log_working(f"Материал {material_id} доступен для стриминга")
                    else:
                        self.log_issue(f"Проблема доступа к материалу {material_id}: {access_response.status_code}")
                        
        except Exception as e:
            self.log_issue(f"Ошибка проверки материалов: {str(e)}")
    
    def test_cors_and_headers(self):
        """Тестирование CORS и заголовков"""
        print("\n🌐 ТЕСТИРОВАНИЕ CORS И ЗАГОЛОВКОВ")
        
        try:
            # Test CORS on video endpoint
            cors_response = self.session.options(f"{BACKEND_URL}/video/test-id")
            cors_headers = cors_response.headers
            
            if cors_headers.get('Access-Control-Allow-Origin'):
                self.log_working("CORS настроен для видео endpoints")
            else:
                self.log_issue("CORS не настроен для видео endpoints")
            
            # Test CORS on materials endpoint
            cors_response = self.session.options(f"{BACKEND_URL}/materials/test-id/stream")
            cors_headers = cors_response.headers
            
            if cors_headers.get('Access-Control-Allow-Origin'):
                self.log_working("CORS настроен для materials endpoints")
            else:
                self.log_issue("CORS не настроен для materials endpoints")
                
        except Exception as e:
            self.log_issue(f"Ошибка проверки CORS: {str(e)}")
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        print("\n" + "="*80)
        print("📋 ФИНАЛЬНЫЙ ОТЧЕТ ДИАГНОСТИКИ")
        print("="*80)
        
        print(f"\n✅ РАБОТАЮЩИЕ ФУНКЦИИ ({len(self.working_features)}):")
        for feature in self.working_features:
            print(f"   ✅ {feature}")
        
        print(f"\n❌ НАЙДЕННЫЕ ПРОБЛЕМЫ ({len(self.issues_found)}):")
        for issue in self.issues_found:
            print(f"   ❌ {issue}")
        
        print(f"\n📊 СТАТИСТИКА:")
        total_checks = len(self.working_features) + len(self.issues_found)
        success_rate = (len(self.working_features) / total_checks * 100) if total_checks > 0 else 0
        print(f"   Всего проверок: {total_checks}")
        print(f"   Успешных: {len(self.working_features)}")
        print(f"   Проблемных: {len(self.issues_found)}")
        print(f"   Успешность: {success_rate:.1f}%")
        
        print(f"\n🎯 ОСНОВНЫЕ ВЫВОДЫ:")
        if len(self.issues_found) == 0:
            print("   ✅ Критических проблем с видео/PDF стримингом не обнаружено")
        elif len(self.issues_found) <= 3:
            print("   ⚠️ Обнаружены минорные проблемы, требующие внимания")
        else:
            print("   ❌ Обнаружены серьезные проблемы с видео/PDF стримингом")
        
        print("="*80)
        
        return success_rate > 70
    
    def run_full_diagnosis(self):
        """Запуск полной диагностики"""
        print("🔬 ЗАПУСК ПОЛНОЙ ДИАГНОСТИКИ ВИДЕО/PDF СТРИМИНГА")
        print("="*80)
        
        if not self.authenticate_users():
            return False
        
        self.diagnose_video_streaming()
        self.diagnose_pdf_streaming()
        self.check_existing_content_issues()
        self.test_cors_and_headers()
        
        return self.generate_final_report()

def main():
    tester = FinalDiagnosisTester()
    success = tester.run_full_diagnosis()
    
    if success:
        print("\n🎉 ДИАГНОСТИКА ЗАВЕРШЕНА: Система работает корректно")
        return 0
    else:
        print("\n💥 ДИАГНОСТИКА ЗАВЕРШЕНА: Обнаружены критические проблемы")
        return 1

if __name__ == "__main__":
    exit(main())