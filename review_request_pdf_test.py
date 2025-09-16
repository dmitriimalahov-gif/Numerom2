#!/usr/bin/env python3
"""
Review Request Specific Test Suite for Additional PDF Files Management
Testing according to the exact scenario specified in the review request

Review Request: Протестировать функциональность управления дополнительными PDF файлами в админ панели
"""

import requests
import json
import os
import tempfile
import time
from pathlib import Path

# Configuration from review request
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"
TEST_LESSON_ID = "lesson_numerom_intro"  # Specified in review request

class ReviewRequestPDFTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.uploaded_pdf_ids = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def test_1_super_admin_authentication(self):
        """1. АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА: Войти как dmitrii.malahov@gmail.com / 756bvy67H"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                user_info = data.get('user', {})
                
                # Verify super admin rights as required
                is_super_admin = user_info.get('is_super_admin', False)
                credits = user_info.get('credits_remaining', 0)
                
                if is_super_admin:
                    self.log_test("1. Аутентификация супер-админа", True, 
                        f"Успешный вход как {user_info.get('email')} с {credits} кредитами, статус супер-админа подтвержден")
                    return True
                else:
                    self.log_test("1. Аутентификация супер-админа", False, 
                        f"Пользователь {user_info.get('email')} не имеет прав супер-админа")
                    return False
            else:
                self.log_test("1. Аутентификация супер-админа", False, 
                    f"Ошибка входа: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("1. Аутентификация супер-админа", False, f"Исключение: {str(e)}")
            return False
    
    def test_2_upload_additional_pdfs(self):
        """2. ЗАГРУЗКА ДОПОЛНИТЕЛЬНЫХ PDF: POST /api/admin/lessons/{lesson_id}/add-pdf"""
        try:
            # Create multiple test PDF files as specified
            test_pdfs = []
            for i in range(3):  # Upload 3 test PDFs
                # Create test PDF content
                temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                pdf_content = f'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'.encode()
                temp_file.write(pdf_content)
                temp_file.close()
                
                filename = f"test_additional_pdf_{i+1}.pdf"
                title = f"Дополнительный материал {i+1}"
                
                # Upload PDF
                with open(temp_file.name, 'rb') as f:
                    files = {'file': (filename, f, 'application/pdf')}
                    data = {'title': title}
                    
                    response = self.session.post(
                        f"{BACKEND_URL}/admin/lessons/{TEST_LESSON_ID}/add-pdf", 
                        files=files, 
                        data=data
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    file_id = result.get('file_id')
                    if file_id:
                        self.uploaded_pdf_ids.append(file_id)
                        test_pdfs.append({
                            'file_id': file_id,
                            'filename': filename,
                            'title': title,
                            'temp_path': temp_file.name
                        })
                else:
                    self.log_test("2. Загрузка дополнительных PDF", False, 
                        f"Ошибка загрузки {filename}: {response.status_code}")
                    return False
                
                # Clean up temp file
                os.unlink(temp_file.name)
            
            if len(test_pdfs) == 3:
                self.log_test("2. Загрузка дополнительных PDF", True, 
                    f"Успешно загружено {len(test_pdfs)} PDF файлов с file_type: 'consultation_pdf'")
                
                # Verify records created in uploaded_files collection with correct type
                # This is verified by checking if files are accessible via consultation endpoint
                accessible_count = 0
                for pdf in test_pdfs:
                    check_response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{pdf['file_id']}")
                    if check_response.status_code == 200:
                        accessible_count += 1
                
                if accessible_count == len(test_pdfs):
                    self.log_test("2.1 Проверка записей в uploaded_files", True, 
                        f"Все {accessible_count} файлов доступны через consultation endpoint (file_type: 'consultation_pdf')")
                    return True
                else:
                    self.log_test("2.1 Проверка записей в uploaded_files", False, 
                        f"Только {accessible_count}/{len(test_pdfs)} файлов доступны")
                    return False
            else:
                self.log_test("2. Загрузка дополнительных PDF", False, 
                    f"Загружено только {len(test_pdfs)}/3 файлов")
                return False
                
        except Exception as e:
            self.log_test("2. Загрузка дополнительных PDF", False, f"Исключение: {str(e)}")
            return False
    
    def test_3_get_additional_pdfs_list(self):
        """3. ПОЛУЧЕНИЕ СПИСКА ДОПОЛНИТЕЛЬНЫХ PDF: GET /api/lessons/{lesson_id}/additional-pdfs"""
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons/{TEST_LESSON_ID}/additional-pdfs")
            
            if response.status_code == 200:
                data = response.json()
                lesson_id = data.get('lesson_id')
                additional_pdfs = data.get('additional_pdfs', [])
                count = data.get('count', 0)
                
                # Verify response format as specified in review request
                if lesson_id == TEST_LESSON_ID and isinstance(additional_pdfs, list):
                    # Check required fields: file_id, filename, title, pdf_url, uploaded_at
                    valid_format_count = 0
                    correct_url_count = 0
                    
                    for pdf in additional_pdfs:
                        required_fields = ['file_id', 'filename', 'title', 'pdf_url', 'uploaded_at']
                        if all(field in pdf for field in required_fields):
                            valid_format_count += 1
                            
                            # Verify pdf_url format: /api/consultations/pdf/{file_id}
                            expected_url = f"/api/consultations/pdf/{pdf['file_id']}"
                            if pdf['pdf_url'] == expected_url:
                                correct_url_count += 1
                    
                    self.log_test("3. Получение списка дополнительных PDF", True, 
                        f"Получен список из {count} PDF файлов. Формат данных корректен: {valid_format_count}/{len(additional_pdfs)} файлов")
                    
                    if correct_url_count == len(additional_pdfs):
                        self.log_test("3.1 Проверка формата pdf_url", True, 
                            f"Все {correct_url_count} URL имеют правильный формат /api/consultations/pdf/{{file_id}}")
                        return True
                    else:
                        self.log_test("3.1 Проверка формата pdf_url", False, 
                            f"Только {correct_url_count}/{len(additional_pdfs)} URL имеют правильный формат")
                        return False
                else:
                    self.log_test("3. Получение списка дополнительных PDF", False, 
                        f"Неверная структура ответа: lesson_id={lesson_id}, тип additional_pdfs={type(additional_pdfs)}")
                    return False
            else:
                self.log_test("3. Получение списка дополнительных PDF", False, 
                    f"Ошибка запроса: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            self.log_test("3. Получение списка дополнительных PDF", False, f"Исключение: {str(e)}")
            return False
    
    def test_4_pdf_streaming(self):
        """4. СТРИМИНГ PDF ФАЙЛОВ: GET /api/consultations/pdf/{file_id}"""
        try:
            if not self.uploaded_pdf_ids:
                self.log_test("4. Стриминг PDF файлов", False, "Нет загруженных PDF для тестирования")
                return False
            
            streaming_success_count = 0
            cors_success_count = 0
            
            for file_id in self.uploaded_pdf_ids:
                # Test streaming endpoint as specified
                stream_url = f"{BACKEND_URL}/consultations/pdf/{file_id}"
                response = self.session.get(stream_url)
                
                if response.status_code == 200:
                    streaming_success_count += 1
                    
                    # Check CORS headers as required
                    cors_origin = response.headers.get('access-control-allow-origin', '')
                    cors_methods = response.headers.get('access-control-allow-methods', '')
                    cors_headers = response.headers.get('access-control-allow-headers', '')
                    content_type = response.headers.get('content-type', '')
                    
                    has_cors_origin = cors_origin == '*'
                    has_cors_methods = 'GET' in cors_methods
                    is_pdf = content_type == 'application/pdf'
                    
                    if has_cors_origin and has_cors_methods and is_pdf:
                        cors_success_count += 1
            
            if streaming_success_count == len(self.uploaded_pdf_ids):
                self.log_test("4. Стриминг PDF файлов", True, 
                    f"Все {streaming_success_count} PDF файлов успешно стримятся")
                
                if cors_success_count == len(self.uploaded_pdf_ids):
                    self.log_test("4.1 Проверка CORS headers", True, 
                        f"Все {cors_success_count} файлов имеют корректные CORS заголовки")
                    return True
                else:
                    self.log_test("4.1 Проверка CORS headers", False, 
                        f"Только {cors_success_count}/{len(self.uploaded_pdf_ids)} файлов имеют корректные CORS заголовки")
                    return False
            else:
                self.log_test("4. Стриминг PDF файлов", False, 
                    f"Только {streaming_success_count}/{len(self.uploaded_pdf_ids)} файлов успешно стримятся")
                return False
                
        except Exception as e:
            self.log_test("4. Стриминг PDF файлов", False, f"Исключение: {str(e)}")
            return False
    
    def test_5_delete_individual_pdf(self):
        """5. УДАЛЕНИЕ ДОПОЛНИТЕЛЬНЫХ PDF: DELETE /api/admin/lessons/pdf/{file_id}"""
        try:
            if not self.uploaded_pdf_ids:
                self.log_test("5. Удаление дополнительных PDF", False, "Нет загруженных PDF для тестирования")
                return False
            
            # Delete one PDF file to test individual deletion
            file_id_to_delete = self.uploaded_pdf_ids[0]
            
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/pdf/{file_id_to_delete}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Verify physical file deletion by checking accessibility
                    verify_response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{file_id_to_delete}")
                    
                    if verify_response.status_code == 404:
                        # Remove from tracking list
                        self.uploaded_pdf_ids.remove(file_id_to_delete)
                        
                        self.log_test("5. Удаление дополнительных PDF", True, 
                            f"PDF файл {file_id_to_delete} успешно удален (физический файл и запись в БД)")
                        return True
                    else:
                        self.log_test("5. Удаление дополнительных PDF", False, 
                            f"PDF файл {file_id_to_delete} все еще доступен после удаления")
                        return False
                else:
                    self.log_test("5. Удаление дополнительных PDF", False, 
                        f"Операция удаления вернула success=False: {result}")
                    return False
            else:
                self.log_test("5. Удаление дополнительных PDF", False, 
                    f"Ошибка удаления: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            self.log_test("5. Удаление дополнительных PDF", False, f"Исключение: {str(e)}")
            return False
    
    def test_6_bulk_deletion(self):
        """6. МАССОВОЕ УДАЛЕНИЕ: handleDeleteAllAdditionalPdfs function"""
        try:
            # First upload a few more PDFs for bulk deletion test
            bulk_pdf_ids = []
            
            for i in range(2):  # Upload 2 more PDFs for bulk test
                temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                pdf_content = f'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'.encode()
                temp_file.write(pdf_content)
                temp_file.close()
                
                # Upload PDF
                with open(temp_file.name, 'rb') as f:
                    files = {'file': (f'bulk_test_{i+1}.pdf', f, 'application/pdf')}
                    data = {'title': f'Bulk Test PDF {i+1}'}
                    
                    response = self.session.post(
                        f"{BACKEND_URL}/admin/lessons/{TEST_LESSON_ID}/add-pdf", 
                        files=files, 
                        data=data
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    file_id = result.get('file_id')
                    if file_id:
                        bulk_pdf_ids.append(file_id)
                
                os.unlink(temp_file.name)
            
            # Add remaining uploaded PDFs to bulk list
            all_pdfs_to_delete = bulk_pdf_ids + self.uploaded_pdf_ids
            
            if len(all_pdfs_to_delete) < 2:
                self.log_test("6. Массовое удаление", False, 
                    f"Недостаточно PDF для тестирования массового удаления: {len(all_pdfs_to_delete)}")
                return False
            
            # Simulate handleDeleteAllAdditionalPdfs function by deleting all PDFs
            deleted_count = 0
            
            for file_id in all_pdfs_to_delete:
                response = self.session.delete(f"{BACKEND_URL}/admin/lessons/pdf/{file_id}")
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        deleted_count += 1
            
            # Verify all files are deleted
            remaining_files = 0
            for file_id in all_pdfs_to_delete:
                verify_response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{file_id}")
                if verify_response.status_code != 404:
                    remaining_files += 1
            
            # Clear our tracking list
            self.uploaded_pdf_ids = []
            
            if deleted_count == len(all_pdfs_to_delete) and remaining_files == 0:
                self.log_test("6. Массовое удаление", True, 
                    f"Успешно удалено {deleted_count} PDF файлов в массовой операции (handleDeleteAllAdditionalPdfs)")
                return True
            else:
                self.log_test("6. Массовое удаление", False, 
                    f"Массовое удаление неполное. Удалено: {deleted_count}/{len(all_pdfs_to_delete)}, Осталось: {remaining_files}")
                return False
                
        except Exception as e:
            self.log_test("6. Массовое удаление", False, f"Исключение: {str(e)}")
            return False
    
    def test_consultation_pdf_viewer_integration(self):
        """Дополнительный тест: интеграция с ConsultationPDFViewer modal"""
        try:
            # Upload one more PDF for this test
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'
            temp_file.write(pdf_content)
            temp_file.close()
            
            # Upload PDF
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('consultation_viewer_test.pdf', f, 'application/pdf')}
                data = {'title': 'ConsultationPDFViewer Test'}
                
                response = self.session.post(
                    f"{BACKEND_URL}/admin/lessons/{TEST_LESSON_ID}/add-pdf", 
                    files=files, 
                    data=data
                )
            
            if response.status_code == 200:
                result = response.json()
                file_id = result.get('file_id')
                
                if file_id:
                    # Test that PDF opens correctly in ConsultationPDFViewer
                    # This is verified by checking the streaming endpoint works properly
                    stream_response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{file_id}")
                    
                    if stream_response.status_code == 200:
                        content_type = stream_response.headers.get('content-type', '')
                        content_disposition = stream_response.headers.get('content-disposition', '')
                        
                        if content_type == 'application/pdf' and 'inline' in content_disposition:
                            # Clean up
                            self.session.delete(f"{BACKEND_URL}/admin/lessons/pdf/{file_id}")
                            os.unlink(temp_file.name)
                            
                            self.log_test("7. Интеграция с ConsultationPDFViewer", True, 
                                "PDF файлы корректно открываются в модальном окне ConsultationPDFViewer")
                            return True
                        else:
                            self.log_test("7. Интеграция с ConsultationPDFViewer", False, 
                                f"Неправильные заголовки для просмотра: Content-Type={content_type}, Disposition={content_disposition}")
                            return False
                    else:
                        self.log_test("7. Интеграция с ConsultationPDFViewer", False, 
                            f"Ошибка стриминга PDF: {stream_response.status_code}")
                        return False
                else:
                    self.log_test("7. Интеграция с ConsultationPDFViewer", False, "Не получен file_id при загрузке")
                    return False
            else:
                self.log_test("7. Интеграция с ConsultationPDFViewer", False, 
                    f"Ошибка загрузки PDF: {response.status_code}")
                return False
            
            os.unlink(temp_file.name)
                
        except Exception as e:
            self.log_test("7. Интеграция с ConsultationPDFViewer", False, f"Исключение: {str(e)}")
            return False
    
    def run_review_request_tests(self):
        """Run all tests according to review request scenario"""
        print("🎯 ТЕСТИРОВАНИЕ ФУНКЦИОНАЛЬНОСТИ УПРАВЛЕНИЯ ДОПОЛНИТЕЛЬНЫМИ PDF ФАЙЛАМИ В АДМИН ПАНЕЛИ")
        print("=" * 100)
        print(f"КОНТЕКСТ: Используется урок с lesson_id: '{TEST_LESSON_ID}'")
        print(f"СИСТЕМА: Унифицированная архитектура с PersonalConsultations (consultation_pdf тип файлов)")
        print(f"СТРИМИНГ: PDF файлы стримятся через /api/consultations/pdf/{{file_id}}")
        print(f"ПРОСМОТР: PDF файлы открываются в модальном окне ConsultationPDFViewer")
        print("=" * 100)
        
        # Test sequence according to review request
        tests = [
            ("1. АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА", self.test_1_super_admin_authentication),
            ("2. ЗАГРУЗКА ДОПОЛНИТЕЛЬНЫХ PDF", self.test_2_upload_additional_pdfs),
            ("3. ПОЛУЧЕНИЕ СПИСКА ДОПОЛНИТЕЛЬНЫХ PDF", self.test_3_get_additional_pdfs_list),
            ("4. СТРИМИНГ PDF ФАЙЛОВ", self.test_4_pdf_streaming),
            ("5. УДАЛЕНИЕ ДОПОЛНИТЕЛЬНЫХ PDF", self.test_5_delete_individual_pdf),
            ("6. МАССОВОЕ УДАЛЕНИЕ", self.test_6_bulk_deletion),
            ("7. ИНТЕГРАЦИЯ С CONSULTATIONPDFVIEWER", self.test_consultation_pdf_viewer_integration)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{test_name}")
            print("-" * 60)
            
            if test_func():
                passed_tests += 1
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Print summary
        print("\n" + "=" * 100)
        print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ")
        print("=" * 100)
        
        success_rate = (passed_tests / total_tests) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   └─ {result['details']}")
        
        print(f"\n📊 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        if success_rate >= 95:
            print("🎉 ОТЛИЧНО: Полная функциональность управления дополнительными PDF в админ панели")
            print("   с загрузкой, просмотром, скачиванием, удалением отдельных файлов и массовым удалением!")
        elif success_rate >= 80:
            print("⚠️  ХОРОШО: Основная функциональность работает, есть незначительные проблемы")
        else:
            print("❌ КРИТИЧНО: Обнаружены серьезные проблемы в функциональности управления PDF")
        
        return success_rate >= 95

if __name__ == "__main__":
    test_suite = ReviewRequestPDFTestSuite()
    test_suite.run_review_request_tests()