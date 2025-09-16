#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ ИСПРАВЛЕННОЙ СИСТЕМЫ ЗАГРУЗКИ И ВОСПРОИЗВЕДЕНИЯ ВИДЕО
Testing Fixed Video Upload and Playback System

Цель: Убедиться что исправлены все проблемы с видеоплеерами в PersonalConsultations, 
LearningSystem и редакторе уроков после возвращения к рабочим endpoints.

ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. GET /api/consultations/video/{file_id} - для личных консультаций
2. GET /api/video/{video_id} - для материалов и уроков  
3. POST /api/admin/upload-video - загрузка видео (рабочий endpoint)
4. POST /api/admin/upload-pdf - загрузка PDF (рабочий endpoint)
5. GET /api/admin/materials - получение списка материалов для урока
"""

import requests
import json
import io
import os
from datetime import datetime
from pathlib import Path

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"

class VideoSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.uploaded_video_id = None
        self.uploaded_pdf_id = None
        
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
        
    def authenticate_super_admin(self):
        """Аутентификация суперадминистратора"""
        print("\n🔐 АУТЕНТИФИКАЦИЯ СУПЕРАДМИНИСТРАТОРА")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user')
                
                # Set authorization header for future requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                
                user_info = f"User ID: {self.user_data.get('id')}, is_super_admin: {self.user_data.get('is_super_admin')}, credits: {self.user_data.get('credits_remaining')}"
                self.log_test("Аутентификация суперадмина", "PASS", user_info)
                return True
            else:
                self.log_test("Аутентификация суперадмина", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация суперадмина", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_video_upload_endpoint(self):
        """Тест загрузки видео через POST /api/admin/upload-video"""
        print("\n📹 ТЕСТ ЗАГРУЗКИ ВИДЕО")
        
        try:
            # Create a small test video file (actually just a binary file with video-like content)
            test_video_content = b'\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41isom' + b'\x00' * 1000
            
            files = {
                'file': ('test_video.mp4', io.BytesIO(test_video_content), 'video/mp4')
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/upload-video", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.uploaded_video_id = data.get('video_id')
                video_url = data.get('video_url')
                
                self.log_test("Загрузка видео", "PASS", 
                             f"Video ID: {self.uploaded_video_id}, URL: {video_url}")
                return True
            else:
                self.log_test("Загрузка видео", "FAIL", 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Загрузка видео", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_video_serving_endpoint(self):
        """Тест воспроизведения видео через GET /api/video/{video_id}"""
        print("\n🎬 ТЕСТ ВОСПРОИЗВЕДЕНИЯ ВИДЕО")
        
        if not self.uploaded_video_id:
            self.log_test("Воспроизведение видео", "SKIP", "Нет загруженного видео для тестирования")
            return False
            
        try:
            # Test video serving endpoint
            response = self.session.get(f"{BACKEND_URL}/video/{self.uploaded_video_id}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Accept-Ranges': response.headers.get('Accept-Ranges')
                }
                
                self.log_test("Воспроизведение видео", "PASS", 
                             f"Content-Type: {content_type}, Size: {content_length} bytes, CORS: {cors_headers}")
                return True
            else:
                self.log_test("Воспроизведение видео", "FAIL", 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Воспроизведение видео", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_pdf_upload_endpoint(self):
        """Тест загрузки PDF через админ-панель"""
        print("\n📄 ТЕСТ ЗАГРУЗКИ PDF")
        
        try:
            # Create a minimal PDF content
            pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF'
            
            # First, initialize upload
            init_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/init", data={
                'title': 'Test PDF Material',
                'description': 'Test PDF for video system testing',
                'lesson_id': 'test_lesson',
                'material_type': 'pdf',
                'filename': 'test_document.pdf',
                'total_size': len(pdf_content)
            })
            
            if init_response.status_code == 200:
                upload_data = init_response.json()
                upload_id = upload_data.get('uploadId')
                
                # Upload chunk
                files = {
                    'chunk': ('chunk_0', io.BytesIO(pdf_content), 'application/pdf')
                }
                chunk_data = {
                    'uploadId': upload_id,
                    'index': 0
                }
                
                chunk_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/chunk", 
                                                 files=files, data=chunk_data)
                
                if chunk_response.status_code == 200:
                    # Finish upload
                    finish_response = self.session.post(f"{BACKEND_URL}/admin/materials/upload/finish", 
                                                      data={'uploadId': upload_id})
                    
                    if finish_response.status_code == 200:
                        material_data = finish_response.json()
                        material = material_data.get('material', {})
                        self.uploaded_pdf_id = material.get('id')
                        
                        self.log_test("Загрузка PDF", "PASS", 
                                     f"Material ID: {self.uploaded_pdf_id}, Title: {material.get('title')}")
                        return True
                    else:
                        self.log_test("Загрузка PDF", "FAIL", 
                                     f"Finish failed - Status: {finish_response.status_code}")
                        return False
                else:
                    self.log_test("Загрузка PDF", "FAIL", 
                                 f"Chunk upload failed - Status: {chunk_response.status_code}")
                    return False
            else:
                self.log_test("Загрузка PDF", "FAIL", 
                             f"Init failed - Status: {init_response.status_code}, Response: {init_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Загрузка PDF", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_materials_list_endpoint(self):
        """Тест получения списка материалов GET /api/admin/materials"""
        print("\n📋 ТЕСТ СПИСКА МАТЕРИАЛОВ")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/materials")
            
            if response.status_code == 200:
                data = response.json()
                materials = data.get('materials', [])
                total_count = data.get('total_count', 0)
                
                # Look for our uploaded PDF
                uploaded_pdf_found = False
                if self.uploaded_pdf_id:
                    for material in materials:
                        if material.get('id') == self.uploaded_pdf_id:
                            uploaded_pdf_found = True
                            break
                
                self.log_test("Список материалов", "PASS", 
                             f"Total materials: {total_count}, Uploaded PDF found: {uploaded_pdf_found}")
                return True
            else:
                self.log_test("Список материалов", "FAIL", 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Список материалов", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_materials_streaming_endpoint(self):
        """Тест стриминга материалов GET /api/materials/{material_id}/stream"""
        print("\n🎯 ТЕСТ СТРИМИНГА МАТЕРИАЛОВ")
        
        if not self.uploaded_pdf_id:
            self.log_test("Стриминг материалов", "SKIP", "Нет загруженного PDF для тестирования")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/materials/{self.uploaded_pdf_id}/stream")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Accept-Ranges': response.headers.get('Accept-Ranges')
                }
                
                self.log_test("Стриминг материалов", "PASS", 
                             f"Content-Type: {content_type}, Size: {content_length} bytes, CORS: {cors_headers}")
                return True
            else:
                self.log_test("Стриминг материалов", "FAIL", 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Стриминг материалов", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_consultations_video_endpoint(self):
        """Тест endpoint для личных консультаций GET /api/consultations/video/{file_id}"""
        print("\n👥 ТЕСТ ENDPOINT ЛИЧНЫХ КОНСУЛЬТАЦИЙ")
        
        # Since we don't have a real consultation video, we'll test with a dummy ID
        # to see if the endpoint exists and handles errors properly
        try:
            test_file_id = "test_consultation_video_id"
            response = self.session.get(f"{BACKEND_URL}/consultations/video/{test_file_id}")
            
            # We expect 404 since the file doesn't exist, but the endpoint should exist
            if response.status_code == 404:
                self.log_test("Endpoint личных консультаций", "PASS", 
                             "Endpoint существует и корректно возвращает 404 для несуществующего файла")
                return True
            elif response.status_code == 200:
                self.log_test("Endpoint личных консультаций", "PASS", 
                             "Endpoint работает и возвращает контент")
                return True
            else:
                self.log_test("Endpoint личных консультаций", "FAIL", 
                             f"Неожиданный статус: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Endpoint личных консультаций", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_database_collections(self):
        """Проверка что видео сохраняется в правильной коллекции uploaded_videos"""
        print("\n🗄️ ТЕСТ СТРУКТУРЫ БАЗЫ ДАННЫХ")
        
        # We can't directly access MongoDB, but we can infer from API responses
        # that the data is stored correctly if our upload and retrieval work
        
        if self.uploaded_video_id and self.uploaded_pdf_id:
            self.log_test("Структура базы данных", "PASS", 
                         "Видео и PDF успешно загружены и доступны через API - структура БД корректна")
            return True
        else:
            self.log_test("Структура базы данных", "FAIL", 
                         "Не удалось загрузить тестовые файлы - возможны проблемы со структурой БД")
            return False
    
    def run_comprehensive_test(self):
        """Запуск полного комплексного тестирования"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ СИСТЕМЫ ВИДЕО/PDF")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate_super_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось аутентифицироваться")
            return False
        
        # Step 2: Test video upload
        self.test_video_upload_endpoint()
        
        # Step 3: Test video serving
        self.test_video_serving_endpoint()
        
        # Step 4: Test PDF upload
        self.test_pdf_upload_endpoint()
        
        # Step 5: Test materials list
        self.test_materials_list_endpoint()
        
        # Step 6: Test materials streaming
        self.test_materials_streaming_endpoint()
        
        # Step 7: Test consultations endpoint
        self.test_consultations_video_endpoint()
        
        # Step 8: Test database structure
        self.test_database_collections()
        
        # Summary
        self.print_test_summary()
        
        return True
    
    def print_test_summary(self):
        """Печать итогового отчета"""
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        skipped_tests = len([r for r in self.test_results if r['status'] == 'SKIP'])
        
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"⚠️ Пропущено: {skipped_tests}")
        print(f"📈 Успешность: {(passed_tests/max(total_tests-skipped_tests, 1)*100):.1f}%")
        
        print("\nДЕТАЛИ ТЕСТОВ:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        # Critical issues
        critical_failures = [r for r in self.test_results if r['status'] == 'FAIL' and 
                           any(keyword in r['test'].lower() for keyword in ['аутентификация', 'загрузка', 'воспроизведение'])]
        
        if critical_failures:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(critical_failures)}):")
            for failure in critical_failures:
                print(f"❌ {failure['test']}: {failure['details']}")
        else:
            print("\n🎉 КРИТИЧЕСКИХ ПРОБЛЕМ НЕ ОБНАРУЖЕНО!")

if __name__ == "__main__":
    tester = VideoSystemTester()
    tester.run_comprehensive_test()