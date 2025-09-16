#!/usr/bin/env python3
"""
FOCUSED STREAMING TEST: Диагностика конкретных проблем с видео/PDF стримингом
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
TEST_ADMIN_PASSWORD = "756bvy67H"

class FocusedStreamingTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        
    def authenticate_admin(self):
        """Authenticate admin"""
        try:
            login_data = {
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                print(f"✅ Admin authenticated: {data.get('user', {}).get('id')}")
                return True
            else:
                print(f"❌ Admin auth failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Admin auth error: {str(e)}")
            return False
    
    def check_database_content(self):
        """Check what's actually in the database"""
        print("\n🔍 ПРОВЕРКА СОДЕРЖИМОГО БАЗЫ ДАННЫХ")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Check lessons
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/lessons", headers=headers)
            if response.status_code == 200:
                lessons = response.json()
                print(f"📚 Уроков в базе: {len(lessons)}")
                for lesson in lessons:
                    print(f"   - ID: {lesson.get('id')}")
                    print(f"     Title: {lesson.get('title')}")
                    print(f"     Video URL: {lesson.get('video_url', 'НЕТ')}")
                    print(f"     Level: {lesson.get('level')}")
                    print(f"     Active: {lesson.get('is_active')}")
                    print()
            else:
                print(f"❌ Не удалось получить уроки: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка получения уроков: {str(e)}")
        
        # Check materials
        try:
            response = self.session.get(f"{BACKEND_URL}/materials", headers=headers)
            if response.status_code == 200:
                materials = response.json()
                print(f"📄 Материалов в базе: {len(materials)}")
                for material in materials:
                    print(f"   - ID: {material.get('id')}")
                    print(f"     Title: {material.get('title')}")
                    print(f"     Type: {material.get('material_type', 'НЕТ')}")
                    print(f"     File URL: {material.get('file_url', 'НЕТ')}")
                    print(f"     File Name: {material.get('file_name', 'НЕТ')}")
                    print()
            else:
                print(f"❌ Не удалось получить материалы: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка получения материалов: {str(e)}")
        
        # Check uploaded videos
        try:
            # This endpoint might not exist, but let's try
            response = self.session.get(f"{BACKEND_URL}/admin/videos", headers=headers)
            if response.status_code == 200:
                videos = response.json()
                print(f"🎥 Загруженных видео: {len(videos)}")
                for video in videos:
                    print(f"   - ID: {video.get('id')}")
                    print(f"     Filename: {video.get('original_filename')}")
                    print(f"     Path: {video.get('file_path')}")
                    print()
            else:
                print(f"ℹ️ Endpoint /admin/videos не существует или недоступен: {response.status_code}")
        except Exception as e:
            print(f"ℹ️ Endpoint /admin/videos недоступен: {str(e)}")
    
    def test_specific_endpoints(self):
        """Test the specific endpoints mentioned in the review request"""
        print("\n🎯 ТЕСТИРОВАНИЕ КОНКРЕТНЫХ ENDPOINTS ИЗ REVIEW REQUEST")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test 1: GET /api/lessons (mentioned in review request)
        print("\n1. Тестирование GET /api/lessons")
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                lessons = response.json()
                print(f"   Response: {json.dumps(lessons, indent=2, ensure_ascii=False)[:500]}...")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {str(e)}")
        
        # Test 2: GET /api/learning/levels (alternative lessons endpoint)
        print("\n2. Тестирование GET /api/learning/levels")
        try:
            response = self.session.get(f"{BACKEND_URL}/learning/levels", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                lessons = data.get('available_lessons', [])
                print(f"   Найдено уроков: {len(lessons)}")
                for lesson in lessons[:2]:  # Show first 2
                    print(f"     - ID: {lesson.get('id')}, Title: {lesson.get('title')}, Video: {lesson.get('video_url', 'НЕТ')}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {str(e)}")
        
        # Test 3: Try to create a test video to test streaming
        print("\n3. Попытка создать тестовое видео")
        try:
            # Create a simple test video file content (just some bytes)
            test_video_content = b"FAKE_VIDEO_CONTENT_FOR_TESTING" * 100
            
            files = {
                'file': ('test_video.mp4', test_video_content, 'video/mp4')
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/upload-video", files=files, headers=headers)
            print(f"   Upload Status: {response.status_code}")
            
            if response.status_code == 200:
                video_data = response.json()
                video_id = video_data.get('video_id')
                video_url = video_data.get('video_url')
                print(f"   ✅ Видео создано: ID={video_id}, URL={video_url}")
                
                # Now test streaming this video
                print(f"\n4. Тестирование стриминга созданного видео")
                stream_response = self.session.get(f"{BACKEND_URL}/video/{video_id}")
                print(f"   Stream Status: {stream_response.status_code}")
                print(f"   Content-Type: {stream_response.headers.get('content-type')}")
                print(f"   Content-Length: {stream_response.headers.get('content-length')}")
                
                if stream_response.status_code == 200:
                    print(f"   ✅ Стриминг видео работает!")
                else:
                    print(f"   ❌ Стриминг видео не работает: {stream_response.text}")
                    
            else:
                print(f"   ❌ Не удалось создать видео: {response.text}")
                
        except Exception as e:
            print(f"   Exception при создании видео: {str(e)}")
        
        # Test 4: Try to create a test PDF material
        print("\n5. Попытка создать тестовый PDF материал")
        try:
            # Create a simple PDF-like content
            test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
            
            # First initialize upload
            init_data = {
                'title': 'Test PDF Material',
                'description': 'Test PDF for streaming',
                'lesson_id': '',
                'material_type': 'pdf',
                'filename': 'test.pdf',
                'total_size': len(test_pdf_content)
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/init", data=init_data, headers=headers)
            print(f"   Init Status: {response.status_code}")
            
            if response.status_code == 200:
                upload_data = response.json()
                upload_id = upload_data.get('uploadId')
                print(f"   Upload ID: {upload_id}")
                
                # Upload chunk
                chunk_data = {
                    'uploadId': upload_id,
                    'index': 0
                }
                files = {
                    'chunk': ('chunk_0', test_pdf_content, 'application/octet-stream')
                }
                
                chunk_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/chunk", data=chunk_data, files=files, headers=headers)
                print(f"   Chunk Status: {chunk_response.status_code}")
                
                if chunk_response.status_code == 200:
                    # Finish upload
                    finish_data = {'uploadId': upload_id}
                    finish_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/finish", data=finish_data, headers=headers)
                    print(f"   Finish Status: {finish_response.status_code}")
                    
                    if finish_response.status_code == 200:
                        material_data = finish_response.json()
                        material = material_data.get('material', {})
                        material_id = material.get('id')
                        print(f"   ✅ PDF материал создан: ID={material_id}")
                        
                        # Test streaming this PDF
                        print(f"\n6. Тестирование стриминга созданного PDF")
                        stream_response = self.session.get(f"{BACKEND_URL}/materials/{material_id}/stream", headers=headers)
                        print(f"   Stream Status: {stream_response.status_code}")
                        print(f"   Content-Type: {stream_response.headers.get('content-type')}")
                        print(f"   Content-Length: {stream_response.headers.get('content-length')}")
                        
                        if stream_response.status_code == 200:
                            print(f"   ✅ Стриминг PDF работает!")
                        else:
                            print(f"   ❌ Стриминг PDF не работает: {stream_response.text}")
                    else:
                        print(f"   ❌ Не удалось завершить загрузку: {finish_response.text}")
                else:
                    print(f"   ❌ Не удалось загрузить chunk: {chunk_response.text}")
            else:
                print(f"   ❌ Не удалось инициализировать загрузку: {response.text}")
                
        except Exception as e:
            print(f"   Exception при создании PDF: {str(e)}")
    
    def test_student_access(self):
        """Test access as a regular student"""
        print("\n👨‍🎓 ТЕСТИРОВАНИЕ ДОСТУПА СТУДЕНТА")
        
        # Create a test student
        try:
            student_data = {
                "email": "test.student.streaming@example.com",
                "password": "testpass123",
                "full_name": "Test Student Streaming",
                "birth_date": "15.03.1990",
                "city": "Москва",
                "phone_number": "+7900123456"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=student_data)
            
            if response.status_code == 200:
                data = response.json()
                student_token = data.get('access_token')
                student_info = data.get('user')
                print(f"✅ Студент создан: ID={student_info.get('id')}, Credits={student_info.get('credits_remaining')}")
                
                # Test student access to materials
                student_headers = {'Authorization': f'Bearer {student_token}'}
                
                # Test materials list
                materials_response = self.session.get(f"{BACKEND_URL}/materials", headers=student_headers)
                print(f"   Materials list status: {materials_response.status_code}")
                
                if materials_response.status_code == 200:
                    materials = materials_response.json()
                    print(f"   Студент видит {len(materials)} материалов")
                    
                    # Try to access first material
                    if materials:
                        material_id = materials[0].get('id')
                        stream_response = self.session.get(f"{BACKEND_URL}/materials/{material_id}/stream", headers=student_headers)
                        print(f"   Доступ к материалу {material_id}: {stream_response.status_code}")
                        if stream_response.status_code != 200:
                            print(f"     Error: {stream_response.text}")
                
                # Test lessons access
                lessons_response = self.session.get(f"{BACKEND_URL}/learning/levels", headers=student_headers)
                print(f"   Lessons access status: {lessons_response.status_code}")
                
                if lessons_response.status_code == 200:
                    data = lessons_response.json()
                    lessons = data.get('available_lessons', [])
                    print(f"   Студент видит {len(lessons)} уроков")
                    
                    # Try to start first lesson
                    if lessons:
                        lesson_id = lessons[0].get('id')
                        start_response = self.session.post(f"{BACKEND_URL}/learning/lesson/{lesson_id}/start", headers=student_headers)
                        print(f"   Начало урока {lesson_id}: {start_response.status_code}")
                        if start_response.status_code != 200:
                            print(f"     Error: {start_response.text}")
                
            else:
                print(f"❌ Не удалось создать студента: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Ошибка тестирования студента: {str(e)}")
    
    def run_focused_tests(self):
        """Run all focused tests"""
        print("🎯 ЗАПУСК ФОКУСИРОВАННОГО ТЕСТИРОВАНИЯ СТРИМИНГА")
        print("=" * 60)
        
        if not self.authenticate_admin():
            print("❌ Не удалось аутентифицировать администратора")
            return False
        
        self.check_database_content()
        self.test_specific_endpoints()
        self.test_student_access()
        
        print("\n" + "=" * 60)
        print("🏁 ФОКУСИРОВАННОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        
        return True

def main():
    tester = FocusedStreamingTester()
    tester.run_focused_tests()

if __name__ == "__main__":
    main()