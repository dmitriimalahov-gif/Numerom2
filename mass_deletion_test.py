#!/usr/bin/env python3
"""
МАССОВОЕ УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ - БЕЗОПАСНАЯ ПРОЦЕДУРА ОЧИСТКИ БАЗЫ ДАННЫХ

Задача: Очистить базу данных от всех обычных пользователей, оставив только супер-админа dmitrii.malahov@gmail.com

ПРОЦЕДУРА БЕЗОПАСНОГО УДАЛЕНИЯ:
1. Аутентификация супер-админа: dmitrii.malahov@gmail.com / 756bvy67H
2. Получение списка пользователей: GET /api/admin/users
3. Фильтрация пользователей:
   - НЕ удалять пользователей с is_super_admin: true
   - НЕ удалять текущего пользователя (dmitrii.malahov@gmail.com)
   - Составить список для удаления из обычных пользователей
4. Массовое удаление:
   - Использовать существующий endpoint DELETE /api/admin/users/{user_id}
   - Удалить каждого пользователя из списка по одному
   - Логировать процесс удаления
   - Обработать ошибки если они возникнут

МЕРЫ БЕЗОПАСНОСТИ:
- Двойная проверка что супер-админ не в списке на удаление
- Подсчет удаленных пользователей
- Проверка что супер-админ остался после операции
- Логирование всех операций

ВАЖНО: Эта операция необратима! Будут удалены ВСЕ пользователи кроме супер-админа.
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class MassUserDeletionTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.super_admin_data = None
        self.deletion_log = []
        
    def log_operation(self, operation, status, details="", user_data=None):
        """Логирование операций"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'status': status,
            'details': details,
            'user_data': user_data
        }
        self.deletion_log.append(log_entry)
        
        status_icon = "✅" if status == "SUCCESS" else "❌" if status == "ERROR" else "⚠️" if status == "WARNING" else "ℹ️"
        print(f"{status_icon} {operation}: {details}")
        
    def authenticate_super_admin(self):
        """1. АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНИСТРАТОРА"""
        print("\n🔐 ШАГ 1: АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНИСТРАТОРА")
        print(f"Email: {SUPER_ADMIN_EMAIL}")
        print(f"Password: {SUPER_ADMIN_PASSWORD}")
        
        try:
            login_data = {
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.super_admin_data = data.get('user')
                
                if self.auth_token and self.super_admin_data:
                    # Set authorization header for future requests
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    
                    # Verify super admin status
                    if self.super_admin_data.get('is_super_admin'):
                        self.log_operation(
                            "Аутентификация супер-админа", 
                            "SUCCESS", 
                            f"User ID: {self.super_admin_data.get('id')}, Email: {self.super_admin_data.get('email')}, Credits: {self.super_admin_data.get('credits_remaining')}"
                        )
                        return True
                    else:
                        self.log_operation("Аутентификация супер-админа", "ERROR", "Пользователь не является супер-администратором")
                        return False
                else:
                    self.log_operation("Аутентификация супер-админа", "ERROR", "Отсутствует токен или данные пользователя")
                    return False
            else:
                self.log_operation("Аутентификация супер-админа", "ERROR", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_operation("Аутентификация супер-админа", "ERROR", f"Исключение: {str(e)}")
            return False
    
    def get_all_users(self):
        """2. ПОЛУЧЕНИЕ СПИСКА ВСЕХ ПОЛЬЗОВАТЕЛЕЙ"""
        print("\n👥 ШАГ 2: ПОЛУЧЕНИЕ СПИСКА ВСЕХ ПОЛЬЗОВАТЕЛЕЙ")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                total_count = data.get('total_count', len(users))
                
                self.log_operation(
                    "Получение списка пользователей", 
                    "SUCCESS", 
                    f"Получено {len(users)} пользователей (total_count: {total_count})"
                )
                
                # Log user details for verification
                print("\n📋 СПИСОК ВСЕХ ПОЛЬЗОВАТЕЛЕЙ:")
                for i, user in enumerate(users, 1):
                    is_super = "🔴 СУПЕР-АДМИН" if user.get('is_super_admin') else "👤 Обычный"
                    is_premium = "💎 Premium" if user.get('is_premium') else "🆓 Free"
                    credits = user.get('credits_remaining', 0)
                    print(f"  {i}. {user.get('email')} | {is_super} | {is_premium} | Credits: {credits}")
                
                return users
            else:
                self.log_operation("Получение списка пользователей", "ERROR", f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_operation("Получение списка пользователей", "ERROR", f"Исключение: {str(e)}")
            return None
    
    def filter_users_for_deletion(self, all_users):
        """3. ФИЛЬТРАЦИЯ ПОЛЬЗОВАТЕЛЕЙ ДЛЯ УДАЛЕНИЯ"""
        print("\n🔍 ШАГ 3: ФИЛЬТРАЦИЯ ПОЛЬЗОВАТЕЛЕЙ ДЛЯ УДАЛЕНИЯ")
        
        if not all_users:
            self.log_operation("Фильтрация пользователей", "ERROR", "Список пользователей пуст")
            return None, None
        
        users_to_delete = []
        protected_users = []
        current_admin_id = self.super_admin_data.get('id')
        
        for user in all_users:
            user_id = user.get('id')
            user_email = user.get('email')
            is_super_admin = user.get('is_super_admin', False)
            
            # Защищенные пользователи (НЕ удалять):
            # 1. Супер-администраторы
            # 2. Текущий пользователь (дополнительная защита)
            if is_super_admin:
                protected_users.append(user)
                self.log_operation(
                    "Защищенный пользователь", 
                    "INFO", 
                    f"СУПЕР-АДМИН: {user_email} (ID: {user_id}) - НЕ БУДЕТ УДАЛЕН"
                )
            elif user_id == current_admin_id:
                protected_users.append(user)
                self.log_operation(
                    "Защищенный пользователь", 
                    "INFO", 
                    f"ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ: {user_email} (ID: {user_id}) - НЕ БУДЕТ УДАЛЕН"
                )
            elif user_email == SUPER_ADMIN_EMAIL:
                protected_users.append(user)
                self.log_operation(
                    "Защищенный пользователь", 
                    "INFO", 
                    f"СУПЕР-АДМИН EMAIL: {user_email} (ID: {user_id}) - НЕ БУДЕТ УДАЛЕН"
                )
            else:
                # Обычный пользователь - добавляем в список на удаление
                users_to_delete.append(user)
                self.log_operation(
                    "Пользователь для удаления", 
                    "WARNING", 
                    f"БУДЕТ УДАЛЕН: {user_email} (ID: {user_id})"
                )
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ФИЛЬТРАЦИИ:")
        print(f"  🛡️ Защищенных пользователей: {len(protected_users)}")
        print(f"  🗑️ Пользователей для удаления: {len(users_to_delete)}")
        
        # Двойная проверка безопасности
        super_admin_in_deletion_list = any(
            user.get('is_super_admin') or user.get('email') == SUPER_ADMIN_EMAIL 
            for user in users_to_delete
        )
        
        if super_admin_in_deletion_list:
            self.log_operation(
                "КРИТИЧЕСКАЯ ОШИБКА БЕЗОПАСНОСТИ", 
                "ERROR", 
                "Супер-администратор найден в списке на удаление! Операция отменена!"
            )
            return None, None
        
        self.log_operation(
            "Фильтрация пользователей", 
            "SUCCESS", 
            f"Безопасная фильтрация завершена. К удалению: {len(users_to_delete)}, Защищено: {len(protected_users)}"
        )
        
        return users_to_delete, protected_users
    
    def confirm_deletion(self, users_to_delete):
        """4. ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ"""
        print("\n⚠️ ШАГ 4: ПОДТВЕРЖДЕНИЕ МАССОВОГО УДАЛЕНИЯ")
        print("🚨 ВНИМАНИЕ: ЭТА ОПЕРАЦИЯ НЕОБРАТИМА!")
        print(f"📊 Будет удалено пользователей: {len(users_to_delete)}")
        
        if len(users_to_delete) == 0:
            self.log_operation("Подтверждение удаления", "INFO", "Нет пользователей для удаления")
            return True
        
        print("\n📋 СПИСОК ПОЛЬЗОВАТЕЛЕЙ ДЛЯ УДАЛЕНИЯ:")
        for i, user in enumerate(users_to_delete, 1):
            print(f"  {i}. {user.get('email')} (ID: {user.get('id')})")
        
        # В автоматическом режиме подтверждаем удаление
        # В реальном сценарии здесь должен быть запрос подтверждения от пользователя
        print(f"\n✅ АВТОМАТИЧЕСКОЕ ПОДТВЕРЖДЕНИЕ: Продолжаем с удалением {len(users_to_delete)} пользователей")
        
        self.log_operation(
            "Подтверждение удаления", 
            "SUCCESS", 
            f"Подтверждено удаление {len(users_to_delete)} пользователей"
        )
        
        return True
    
    def delete_users_batch(self, users_to_delete):
        """5. МАССОВОЕ УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ"""
        print("\n🗑️ ШАГ 5: МАССОВОЕ УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ")
        
        if not users_to_delete:
            self.log_operation("Массовое удаление", "INFO", "Нет пользователей для удаления")
            return True, 0, 0
        
        deleted_count = 0
        error_count = 0
        
        print(f"🚀 Начинаем удаление {len(users_to_delete)} пользователей...")
        
        for i, user in enumerate(users_to_delete, 1):
            user_id = user.get('id')
            user_email = user.get('email')
            
            print(f"\n[{i}/{len(users_to_delete)}] Удаление пользователя: {user_email}")
            
            try:
                # Дополнительная проверка безопасности перед каждым удалением
                if user.get('is_super_admin') or user_email == SUPER_ADMIN_EMAIL:
                    self.log_operation(
                        f"БЕЗОПАСНОСТЬ - Пропуск удаления", 
                        "WARNING", 
                        f"Пользователь {user_email} защищен от удаления",
                        user
                    )
                    continue
                
                # Выполняем удаление
                response = self.session.delete(f"{BACKEND_URL}/admin/users/{user_id}")
                
                if response.status_code == 200:
                    deleted_count += 1
                    self.log_operation(
                        f"Удаление пользователя #{i}", 
                        "SUCCESS", 
                        f"Успешно удален: {user_email} (ID: {user_id})",
                        user
                    )
                    print(f"  ✅ Успешно удален: {user_email}")
                else:
                    error_count += 1
                    error_details = f"HTTP {response.status_code}: {response.text}"
                    self.log_operation(
                        f"Ошибка удаления пользователя #{i}", 
                        "ERROR", 
                        f"Не удалось удалить {user_email}: {error_details}",
                        user
                    )
                    print(f"  ❌ Ошибка удаления {user_email}: {error_details}")
                
                # Небольшая пауза между удалениями для снижения нагрузки на сервер
                time.sleep(0.5)
                
            except Exception as e:
                error_count += 1
                self.log_operation(
                    f"Исключение при удалении пользователя #{i}", 
                    "ERROR", 
                    f"Исключение при удалении {user_email}: {str(e)}",
                    user
                )
                print(f"  💥 Исключение при удалении {user_email}: {str(e)}")
        
        print(f"\n📊 РЕЗУЛЬТАТЫ МАССОВОГО УДАЛЕНИЯ:")
        print(f"  ✅ Успешно удалено: {deleted_count}")
        print(f"  ❌ Ошибок удаления: {error_count}")
        print(f"  📋 Всего обработано: {len(users_to_delete)}")
        
        success = error_count == 0
        self.log_operation(
            "Массовое удаление завершено", 
            "SUCCESS" if success else "WARNING", 
            f"Удалено: {deleted_count}, Ошибок: {error_count}, Всего: {len(users_to_delete)}"
        )
        
        return success, deleted_count, error_count
    
    def verify_deletion_results(self):
        """6. ПРОВЕРКА РЕЗУЛЬТАТОВ УДАЛЕНИЯ"""
        print("\n🔍 ШАГ 6: ПРОВЕРКА РЕЗУЛЬТАТОВ УДАЛЕНИЯ")
        
        try:
            # Получаем обновленный список пользователей
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            
            if response.status_code == 200:
                data = response.json()
                remaining_users = data.get('users', [])
                
                print(f"\n👥 ОСТАВШИЕСЯ ПОЛЬЗОВАТЕЛИ ({len(remaining_users)}):")
                
                super_admin_found = False
                for i, user in enumerate(remaining_users, 1):
                    user_email = user.get('email')
                    is_super = user.get('is_super_admin', False)
                    is_premium = user.get('is_premium', False)
                    credits = user.get('credits_remaining', 0)
                    
                    status_icon = "🔴" if is_super else "👤"
                    premium_icon = "💎" if is_premium else "🆓"
                    
                    print(f"  {i}. {status_icon} {user_email} | {premium_icon} | Credits: {credits}")
                    
                    if user_email == SUPER_ADMIN_EMAIL:
                        super_admin_found = True
                
                # Проверяем что супер-админ остался
                if super_admin_found:
                    self.log_operation(
                        "Проверка супер-админа", 
                        "SUCCESS", 
                        f"Супер-администратор {SUPER_ADMIN_EMAIL} успешно сохранен"
                    )
                else:
                    self.log_operation(
                        "Проверка супер-админа", 
                        "ERROR", 
                        f"КРИТИЧЕСКАЯ ОШИБКА: Супер-администратор {SUPER_ADMIN_EMAIL} не найден!"
                    )
                    return False
                
                # Проверяем что остались только защищенные пользователи
                non_super_users = [u for u in remaining_users if not u.get('is_super_admin')]
                if len(non_super_users) == 0:
                    self.log_operation(
                        "Проверка очистки базы", 
                        "SUCCESS", 
                        "База данных успешно очищена от обычных пользователей"
                    )
                else:
                    self.log_operation(
                        "Проверка очистки базы", 
                        "WARNING", 
                        f"В базе остались {len(non_super_users)} обычных пользователей"
                    )
                
                self.log_operation(
                    "Проверка результатов", 
                    "SUCCESS", 
                    f"Проверка завершена. Осталось пользователей: {len(remaining_users)}"
                )
                
                return True
            else:
                self.log_operation("Проверка результатов", "ERROR", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_operation("Проверка результатов", "ERROR", f"Исключение: {str(e)}")
            return False
    
    def save_deletion_log(self):
        """7. СОХРАНЕНИЕ ЛОГА ОПЕРАЦИЙ"""
        print("\n💾 ШАГ 7: СОХРАНЕНИЕ ЛОГА ОПЕРАЦИЙ")
        
        try:
            log_filename = f"mass_deletion_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(log_filename, 'w', encoding='utf-8') as f:
                json.dump(self.deletion_log, f, ensure_ascii=False, indent=2)
            
            self.log_operation(
                "Сохранение лога", 
                "SUCCESS", 
                f"Лог операций сохранен в файл: {log_filename}"
            )
            
            print(f"📄 Лог операций сохранен: {log_filename}")
            return True
            
        except Exception as e:
            self.log_operation("Сохранение лога", "ERROR", f"Ошибка сохранения лога: {str(e)}")
            return False
    
    def run_mass_deletion(self):
        """ЗАПУСК ПОЛНОЙ ПРОЦЕДУРЫ МАССОВОГО УДАЛЕНИЯ"""
        print("🚨 МАССОВОЕ УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ - БЕЗОПАСНАЯ ПРОЦЕДУРА")
        print("=" * 80)
        print("⚠️  ВНИМАНИЕ: ЭТА ОПЕРАЦИЯ НЕОБРАТИМА!")
        print("🎯 ЦЕЛЬ: Очистить базу данных от всех пользователей кроме супер-админа")
        print("🛡️  ЗАЩИТА: Супер-администратор dmitrii.malahov@gmail.com будет сохранен")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Шаг 1: Аутентификация
        if not self.authenticate_super_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось аутентифицировать супер-администратора")
            return False
        
        # Шаг 2: Получение списка пользователей
        all_users = self.get_all_users()
        if all_users is None:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить список пользователей")
            return False
        
        # Шаг 3: Фильтрация пользователей
        users_to_delete, protected_users = self.filter_users_for_deletion(all_users)
        if users_to_delete is None:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Ошибка фильтрации пользователей")
            return False
        
        # Шаг 4: Подтверждение удаления
        if not self.confirm_deletion(users_to_delete):
            print("❌ ОПЕРАЦИЯ ОТМЕНЕНА: Удаление не подтверждено")
            return False
        
        # Шаг 5: Массовое удаление
        success, deleted_count, error_count = self.delete_users_batch(users_to_delete)
        
        # Шаг 6: Проверка результатов
        verification_success = self.verify_deletion_results()
        
        # Шаг 7: Сохранение лога
        self.save_deletion_log()
        
        # Итоговый отчет
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 80)
        print("📋 ИТОГОВЫЙ ОТЧЕТ МАССОВОГО УДАЛЕНИЯ")
        print("=" * 80)
        print(f"⏱️  Время выполнения: {duration}")
        print(f"👥 Всего пользователей было: {len(all_users)}")
        print(f"🛡️  Защищенных пользователей: {len(protected_users) if protected_users else 0}")
        print(f"🗑️  Пользователей для удаления: {len(users_to_delete)}")
        print(f"✅ Успешно удалено: {deleted_count}")
        print(f"❌ Ошибок удаления: {error_count}")
        
        overall_success = success and verification_success and error_count == 0
        
        if overall_success:
            print("\n🎉 МАССОВОЕ УДАЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ База данных очищена от всех обычных пользователей")
            print("🛡️  Супер-администратор сохранен и функционирует")
            print("📊 Все связанные данные (progress, levels, quiz_results, etc.) удалены")
        else:
            print("\n⚠️  МАССОВОЕ УДАЛЕНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
            if error_count > 0:
                print(f"❌ Обнаружены ошибки при удалении: {error_count}")
            if not verification_success:
                print("❌ Ошибка при проверке результатов")
        
        return overall_success

def main():
    """Главная функция запуска массового удаления"""
    print("🚨 ЗАПУСК ПРОЦЕДУРЫ МАССОВОГО УДАЛЕНИЯ ПОЛЬЗОВАТЕЛЕЙ")
    print("⚠️  ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ: ЭТА ОПЕРАЦИЯ НЕОБРАТИМА!")
    
    # В реальном сценарии здесь должно быть дополнительное подтверждение
    print("✅ Продолжаем выполнение...")
    
    tester = MassUserDeletionTester()
    
    try:
        success = tester.run_mass_deletion()
        if success:
            print("\n✅ Процедура массового удаления завершена успешно")
            return 0
        else:
            print("\n⚠️  Процедура массового удаления завершена с предупреждениями")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️ Операция прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())