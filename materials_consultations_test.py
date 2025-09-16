#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ: Материалы в уроках и консультации
Testing Materials in Lessons and Consultations Improvements

Согласно review request, тестируем:
1. КОНСУЛЬТАЦИИ - Выбор студента в админ панели
2. МАТЕРИАЛЫ В УРОКАХ - загрузка через GET /api/materials
3. ВИДЕО МАТЕРИАЛЫ - YouTube URL и PDF файлы
4. НОВЫЕ ТЕСТОВЫЕ ДАННЫЕ - проверка конкретных материалов
"""

import requests
import json
from datetime import datetime
import sys
import uuid

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class MaterialsConsultationsTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.created_test_data = []
        
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
        """Authenticate as super admin"""
        print("\n🔐 АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.user_data = data['user']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                self.log_test(
                    "Аутентификация супер-админа",
                    "PASS",
                    f"Успешный вход: {self.user_data.get('email', 'N/A')}, "
                    f"Кредиты: {self.user_data.get('credits_remaining', 0)}, "
                    f"Супер-админ: {self.user_data.get('is_super_admin', False)}"
                )
                return True
            else:
                self.log_test("Аутентификация супер-админа", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация супер-админа", "FAIL", f"Ошибка: {str(e)}")
            return False

    def test_admin_users_for_consultations(self):
        """1. КОНСУЛЬТАЦИИ - Тест загрузки пользователей для выбора студента"""
        print("\n👥 ТЕСТ 1: ЗАГРУЗКА ПОЛЬЗОВАТЕЛЕЙ ДЛЯ КОНСУЛЬТАЦИЙ")
        
        try:
            # Тестируем GET /api/admin/users для получения списка студентов
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                total_count = data.get('total_count', 0)
                
                if len(users) > 0:
                    # Проверяем структуру данных пользователей
                    first_user = users[0]
                    required_fields = ['id', 'email', 'name', 'credits_remaining']
                    missing_fields = [field for field in required_fields if field not in first_user]
                    
                    if not missing_fields:
                        self.log_test(
                            "Загрузка пользователей для консультаций",
                            "PASS",
                            f"Найдено {len(users)} пользователей с полными данными для select компонента. "
                            f"Поля: {', '.join(required_fields)}"
                        )
                        
                        # Сохраняем данные пользователей для дальнейших тестов
                        self.available_users = users
                        return True
                    else:
                        self.log_test(
                            "Загрузка пользователей для консультаций",
                            "FAIL",
                            f"Отсутствуют обязательные поля: {missing_fields}"
                        )
                        return False
                else:
                    self.log_test(
                        "Загрузка пользователей для консультаций",
                        "FAIL",
                        "Список пользователей пуст - нет студентов для выбора"
                    )
                    return False
            else:
                self.log_test(
                    "Загрузка пользователей для консультаций",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Загрузка пользователей для консультаций",
                "FAIL",
                f"Ошибка: {str(e)}"
            )
            return False

    def test_consultation_creation_with_student_selection(self):
        """2. КОНСУЛЬТАЦИИ - Тест создания консультации с выбором студента"""
        print("\n📝 ТЕСТ 2: СОЗДАНИЕ КОНСУЛЬТАЦИИ С ВЫБОРОМ СТУДЕНТА")
        
        if not hasattr(self, 'available_users') or not self.available_users:
            self.log_test(
                "Создание консультации с выбором студента",
                "SKIP",
                "Нет доступных пользователей для тестирования"
            )
            return False
            
        try:
            # Выбираем первого доступного пользователя
            test_user = self.available_users[0]
            assigned_user_id = test_user['id']
            
            # Создаем тестовую консультацию
            consultation_data = {
                "title": "Тестовая консультация - Выбор студента",
                "description": "Тестирование функции выбора студента при создании консультации",
                "assigned_user_id": assigned_user_id,
                "cost_credits": 100,
                "is_active": True,
                "video_url": "https://www.youtube.com/watch?v=test123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/consultations", json=consultation_data)
            
            if response.status_code == 200:
                created_consultation = response.json()
                consultation_id = created_consultation.get('consultation_id') or created_consultation.get('id')
                
                if consultation_id:
                    self.created_test_data.append(('consultation', consultation_id))
                    
                    self.log_test(
                        "Создание консультации с выбором студента",
                        "PASS",
                        f"Консультация создана с assigned_user_id: {assigned_user_id} "
                        f"для пользователя {test_user.get('email', 'N/A')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Создание консультации с выбором студента",
                        "FAIL",
                        "Консультация создана, но ID не возвращен"
                    )
                    return False
            else:
                self.log_test(
                    "Создание консультации с выбором студента",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Создание консультации с выбором студента",
                "FAIL",
                f"Ошибка: {str(e)}"
            )
            return False

    def test_materials_loading(self):
        """3. МАТЕРИАЛЫ В УРОКАХ - Тест загрузки материалов"""
        print("\n📚 ТЕСТ 3: ЗАГРУЗКА МАТЕРИАЛОВ В УРОКАХ")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                if isinstance(materials, list) and len(materials) > 0:
                    # Анализируем структуру материалов
                    materials_with_lesson_id = [m for m in materials if m.get('lesson_id')]
                    materials_without_lesson_id = [m for m in materials if not m.get('lesson_id')]
                    
                    youtube_materials = [m for m in materials if m.get('video_url') and 'youtube' in m.get('video_url', '').lower()]
                    pdf_materials = [m for m in materials if m.get('file_path') or m.get('material_type') == 'pdf']
                    
                    self.log_test(
                        "Загрузка материалов в уроках",
                        "PASS",
                        f"Найдено {len(materials)} материалов: "
                        f"{len(materials_with_lesson_id)} с lesson_id, "
                        f"{len(materials_without_lesson_id)} без lesson_id, "
                        f"{len(youtube_materials)} YouTube, "
                        f"{len(pdf_materials)} PDF"
                    )
                    
                    # Сохраняем материалы для дальнейшего анализа
                    self.materials_data = materials
                    return True
                else:
                    self.log_test(
                        "Загрузка материалов в уроках",
                        "FAIL",
                        "Материалы не найдены или пустой список"
                    )
                    return False
            else:
                self.log_test(
                    "Загрузка материалов в уроках",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Загрузка материалов в уроках",
                "FAIL",
                f"Ошибка: {str(e)}"
            )
            return False

    def test_specific_test_materials(self):
        """4. НОВЫЕ ТЕСТОВЫЕ ДАННЫЕ - Проверка конкретных материалов"""
        print("\n🎯 ТЕСТ 4: ПРОВЕРКА НОВЫХ ТЕСТОВЫХ МАТЕРИАЛОВ")
        
        if not hasattr(self, 'materials_data'):
            self.log_test(
                "Проверка новых тестовых материалов",
                "SKIP",
                "Материалы не загружены"
            )
            return False
            
        try:
            # Ищем конкретные материалы из review request
            target_materials = [
                "Методология ведической нумерологии",
                "Дополнительное видео: Числа и их энергии"
            ]
            
            found_materials = []
            target_lesson_id = "06d43986-39f7-4b07-b703-e43d3a41d640"
            
            for material in self.materials_data:
                title = material.get('title', '')
                for target_title in target_materials:
                    if target_title.lower() in title.lower():
                        found_materials.append({
                            'title': title,
                            'id': material.get('id'),
                            'lesson_id': material.get('lesson_id'),
                            'video_url': material.get('video_url'),
                            'material_type': material.get('material_type'),
                            'has_youtube': 'youtube' in material.get('video_url', '').lower()
                        })
                        break
            
            # Проверяем материалы с конкретным lesson_id
            lesson_specific_materials = [m for m in self.materials_data if m.get('lesson_id') == target_lesson_id]
            
            if found_materials:
                details = f"Найдено {len(found_materials)} из {len(target_materials)} целевых материалов. "
                details += f"Материалы с lesson_id {target_lesson_id}: {len(lesson_specific_materials)}. "
                
                for material in found_materials:
                    details += f"\n  - {material['title']}: "
                    details += f"YouTube: {'Да' if material['has_youtube'] else 'Нет'}, "
                    details += f"lesson_id: {material['lesson_id'] or 'Нет'}"
                
                self.log_test(
                    "Проверка новых тестовых материалов",
                    "PASS",
                    details
                )
                return True
            else:
                self.log_test(
                    "Проверка новых тестовых материалов",
                    "FAIL",
                    f"Целевые материалы не найдены. Всего материалов: {len(self.materials_data)}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Проверка новых тестовых материалов",
                "FAIL",
                f"Ошибка: {str(e)}"
            )
            return False

    def test_mixed_materials_for_lesson(self):
        """5. СМЕШАННЫЕ МАТЕРИАЛЫ - Тест YouTube + PDF для одного урока"""
        print("\n🎬 ТЕСТ 5: СМЕШАННЫЕ МАТЕРИАЛЫ (YOUTUBE + PDF) ДЛЯ УРОКА")
        
        if not hasattr(self, 'materials_data'):
            self.log_test(
                "Смешанные материалы для урока",
                "SKIP",
                "Материалы не загружены"
            )
            return False
            
        try:
            # Группируем материалы по lesson_id
            lessons_materials = {}
            for material in self.materials_data:
                lesson_id = material.get('lesson_id')
                if lesson_id:
                    if lesson_id not in lessons_materials:
                        lessons_materials[lesson_id] = []
                    lessons_materials[lesson_id].append(material)
            
            # Ищем уроки со смешанными материалами
            mixed_lessons = []
            for lesson_id, materials in lessons_materials.items():
                has_youtube = any('youtube' in m.get('video_url', '').lower() for m in materials)
                has_pdf = any(m.get('material_type') == 'pdf' or m.get('file_path') for m in materials)
                
                if has_youtube and has_pdf:
                    mixed_lessons.append({
                        'lesson_id': lesson_id,
                        'materials_count': len(materials),
                        'youtube_count': sum(1 for m in materials if 'youtube' in m.get('video_url', '').lower()),
                        'pdf_count': sum(1 for m in materials if m.get('material_type') == 'pdf' or m.get('file_path'))
                    })
            
            if mixed_lessons:
                details = f"Найдено {len(mixed_lessons)} уроков со смешанными материалами (YouTube + PDF):"
                for lesson in mixed_lessons:
                    details += f"\n  - Урок {lesson['lesson_id']}: "
                    details += f"{lesson['youtube_count']} YouTube + {lesson['pdf_count']} PDF"
                
                self.log_test(
                    "Смешанные материалы для урока",
                    "PASS",
                    details
                )
                return True
            else:
                # Проверяем есть ли вообще YouTube и PDF материалы отдельно
                total_youtube = sum(1 for m in self.materials_data if 'youtube' in m.get('video_url', '').lower())
                total_pdf = sum(1 for m in self.materials_data if m.get('material_type') == 'pdf' or m.get('file_path'))
                
                self.log_test(
                    "Смешанные материалы для урока",
                    "WARN",
                    f"Смешанные материалы не найдены. Всего YouTube: {total_youtube}, PDF: {total_pdf}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Смешанные материалы для урока",
                "FAIL",
                f"Ошибка: {str(e)}"
            )
            return False

    def test_student_material_access(self):
        """6. ДОСТУП СТУДЕНТОВ - Тест что студенты видят все типы материалов"""
        print("\n👨‍🎓 ТЕСТ 6: ДОСТУП СТУДЕНТОВ К МАТЕРИАЛАМ")
        
        if not hasattr(self, 'materials_data'):
            self.log_test(
                "Доступ студентов к материалам",
                "SKIP",
                "Материалы не загружены"
            )
            return False
            
        try:
            # Анализируем типы материалов доступных студентам
            youtube_materials = []
            pdf_materials = []
            video_lessons = []
            
            for material in self.materials_data:
                # YouTube материалы
                if material.get('video_url') and 'youtube' in material.get('video_url', '').lower():
                    youtube_materials.append(material)
                
                # PDF материалы
                if material.get('material_type') == 'pdf' or material.get('file_path'):
                    pdf_materials.append(material)
                
                # Видео уроки (не YouTube)
                if material.get('video_url') and 'youtube' not in material.get('video_url', '').lower():
                    video_lessons.append(material)
            
            total_types = len([t for t in [youtube_materials, pdf_materials, video_lessons] if t])
            
            if total_types >= 2:  # Минимум 2 из 3 типов должны быть доступны
                details = f"Студенты имеют доступ к {total_types}/3 типам материалов:\n"
                details += f"  - YouTube ссылки: {len(youtube_materials)}\n"
                details += f"  - PDF файлы: {len(pdf_materials)}\n"
                details += f"  - Видео занятия: {len(video_lessons)}"
                
                self.log_test(
                    "Доступ студентов к материалам",
                    "PASS",
                    details
                )
                return True
            else:
                self.log_test(
                    "Доступ студентов к материалам",
                    "FAIL",
                    f"Недостаточно типов материалов: {total_types}/3. "
                    f"YouTube: {len(youtube_materials)}, PDF: {len(pdf_materials)}, Видео: {len(video_lessons)}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Доступ студентов к материалам",
                "FAIL",
                f"Ошибка: {str(e)}"
            )
            return False

    def cleanup_test_data(self):
        """Очистка тестовых данных"""
        print("\n🧹 ОЧИСТКА ТЕСТОВЫХ ДАННЫХ")
        
        for data_type, data_id in self.created_test_data:
            try:
                if data_type == 'consultation':
                    response = self.session.delete(f"{BACKEND_URL}/admin/consultations/{data_id}")
                    if response.status_code in [200, 204, 404]:
                        print(f"✅ Удалена тестовая консультация: {data_id}")
                    else:
                        print(f"⚠️ Не удалось удалить консультацию {data_id}: HTTP {response.status_code}")
            except Exception as e:
                print(f"⚠️ Ошибка при удалении {data_type} {data_id}: {str(e)}")

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ МАТЕРИАЛОВ И КОНСУЛЬТАЦИЙ")
        print("="*80)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARN'])
        skipped = len([r for r in self.test_results if r['status'] == 'SKIP'])
        total = len(self.test_results)
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Всего тестов: {total}")
        print(f"✅ Пройдено: {passed}")
        print(f"❌ Провалено: {failed}")
        print(f"⚠️ Предупреждения: {warnings}")
        print(f"⏭️ Пропущено: {skipped}")
        print(f"📈 Успешность: {success_rate:.1f}%")
        
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️" if result['status'] == "WARN" else "⏭️"
            print(f"{status_icon} {result['test']}")
            if result['details']:
                # Ограничиваем длину деталей для читаемости
                details = result['details']
                if len(details) > 200:
                    details = details[:200] + "..."
                print(f"   {details}")
        
        # Критические проблемы
        critical_failures = [r for r in self.test_results if r['status'] == 'FAIL']
        if critical_failures:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(critical_failures)}):")
            for failure in critical_failures:
                print(f"❌ {failure['test']}: {failure['details']}")
        
        return success_rate >= 80  # Считаем успешным если 80%+ тестов прошли

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ МАТЕРИАЛОВ И КОНСУЛЬТАЦИЙ")
        print("="*80)
        
        # Аутентификация
        if not self.authenticate_super_admin():
            print("❌ Не удалось аутентифицироваться. Тестирование прервано.")
            return False
        
        # Основные тесты
        tests = [
            self.test_admin_users_for_consultations,
            self.test_consultation_creation_with_student_selection,
            self.test_materials_loading,
            self.test_specific_test_materials,
            self.test_mixed_materials_for_lesson,
            self.test_student_material_access
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                test_name = test.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, "FAIL", f"Неожиданная ошибка: {str(e)}")
        
        # Очистка
        self.cleanup_test_data()
        
        # Итоговый отчет
        return self.generate_summary()

def main():
    """Main function"""
    tester = MaterialsConsultationsTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        sys.exit(0)
    else:
        print("\n💥 ТЕСТИРОВАНИЕ ВЫЯВИЛО КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
        sys.exit(1)

if __name__ == "__main__":
    main()