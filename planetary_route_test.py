#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Диагностика ошибок планетарного маршрута
Тестирование месячного и квартального планетарного маршрута согласно review request
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class PlanetaryRouteTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_info = None
        
    def authenticate(self):
        """Аутентификация супер админа"""
        print("🔐 Аутентификация супер админа...")
        
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            print(f"   Статус логина: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.user_info = data.get('user', {})
                
                # Устанавливаем заголовок авторизации
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                })
                
                print(f"   ✅ Успешная аутентификация")
                print(f"   👤 Пользователь: {self.user_info.get('email')}")
                print(f"   🎫 Кредиты: {self.user_info.get('credits_remaining')}")
                print(f"   👑 Супер админ: {self.user_info.get('is_super_admin')}")
                print(f"   💎 Премиум: {self.user_info.get('is_premium')}")
                return True
            else:
                print(f"   ❌ Ошибка логина: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Исключение при логине: {e}")
            return False
    
    def test_daily_route(self, date="2025-08-24", city="Кишинев"):
        """Тестирование дневного планетарного маршрута (для сравнения)"""
        print(f"\n📅 Тестирование ДНЕВНОГО планетарного маршрута...")
        print(f"   Дата: {date}, Город: {city}")
        
        try:
            url = f"{BACKEND_URL}/vedic-time/planetary-route"
            params = {"date": date, "city": city}
            
            response = self.session.get(url, params=params)
            print(f"   Статус код: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Дневной маршрут работает корректно")
                print(f"   📍 Город: {data.get('city', 'N/A')}")
                print(f"   🌟 Правящая планета: {data.get('daily_ruling_planet', 'N/A')}")
                print(f"   ⏰ Лучшие часы: {len(data.get('best_activity_hours', []))} периодов")
                return True
            else:
                print(f"   ❌ Ошибка дневного маршрута: {response.status_code}")
                print(f"   Детали ошибки: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Исключение при тестировании дневного маршрута: {e}")
            return False
    
    def test_monthly_route(self, date="2025-08-24", city="Кишинев"):
        """КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Месячный планетарный маршрут"""
        print(f"\n🗓️ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: МЕСЯЧНЫЙ планетарный маршрут...")
        print(f"   Дата: {date}, Город: {city}")
        
        try:
            url = f"{BACKEND_URL}/vedic-time/planetary-route/monthly"
            params = {"date": date, "city": city}
            
            print(f"   🔗 URL: {url}")
            print(f"   📋 Параметры: {params}")
            
            response = self.session.get(url, params=params, timeout=30)
            print(f"   📊 Статус код: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Месячный маршрут работает!")
                print(f"   📅 Период: {data.get('period', 'N/A')}")
                print(f"   📍 Город: {data.get('city', 'N/A')}")
                print(f"   📈 Всего дней: {data.get('total_days', 'N/A')}")
                
                daily_schedule = data.get('daily_schedule', [])
                print(f"   📋 Дневных расписаний: {len(daily_schedule)}")
                
                if daily_schedule:
                    first_day = daily_schedule[0]
                    print(f"   🌅 Первый день: {first_day.get('date', 'N/A')}")
                    print(f"   🌟 Планета: {first_day.get('ruling_planet', 'N/A')}")
                
                return True
                
            elif response.status_code == 400:
                print(f"   ❌ ОШИБКА 400 - Неверный запрос")
                error_detail = response.text
                print(f"   📝 Детали ошибки: {error_detail}")
                
                try:
                    error_json = response.json()
                    print(f"   🔍 JSON ошибка: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                except:
                    pass
                    
                return False
                
            elif response.status_code == 422:
                print(f"   ❌ ОШИБКА 422 - Ошибка валидации")
                error_detail = response.text
                print(f"   📝 Детали ошибки: {error_detail}")
                
                try:
                    error_json = response.json()
                    print(f"   🔍 JSON ошибка: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                except:
                    pass
                    
                return False
                
            elif response.status_code == 500:
                print(f"   ❌ КРИТИЧЕСКАЯ ОШИБКА 500 - Внутренняя ошибка сервера")
                error_detail = response.text
                print(f"   📝 Детали ошибки: {error_detail}")
                
                try:
                    error_json = response.json()
                    print(f"   🔍 JSON ошибка: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                except:
                    pass
                    
                return False
            else:
                print(f"   ❌ Неожиданный статус код: {response.status_code}")
                print(f"   📝 Ответ: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ ТАЙМАУТ: Запрос превысил 30 секунд")
            return False
        except Exception as e:
            print(f"   ❌ Исключение при тестировании месячного маршрута: {e}")
            return False
    
    def test_quarterly_route(self, date="2025-08-24", city="Кишинев"):
        """КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Квартальный планетарный маршрут"""
        print(f"\n📆 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: КВАРТАЛЬНЫЙ планетарный маршрут...")
        print(f"   Дата: {date}, Город: {city}")
        
        try:
            url = f"{BACKEND_URL}/vedic-time/planetary-route/quarterly"
            params = {"date": date, "city": city}
            
            print(f"   🔗 URL: {url}")
            print(f"   📋 Параметры: {params}")
            
            response = self.session.get(url, params=params, timeout=30)
            print(f"   📊 Статус код: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Квартальный маршрут работает!")
                print(f"   📅 Период: {data.get('period', 'N/A')}")
                print(f"   📍 Город: {data.get('city', 'N/A')}")
                print(f"   📈 Всего дней: {data.get('total_days', 'N/A')}")
                
                daily_schedule = data.get('daily_schedule', [])
                print(f"   📋 Дневных расписаний: {len(daily_schedule)}")
                
                if daily_schedule:
                    first_day = daily_schedule[0]
                    print(f"   🌅 Первый день: {first_day.get('date', 'N/A')}")
                    print(f"   🌟 Планета: {first_day.get('ruling_planet', 'N/A')}")
                
                return True
                
            elif response.status_code == 400:
                print(f"   ❌ ОШИБКА 400 - Неверный запрос")
                error_detail = response.text
                print(f"   📝 Детали ошибки: {error_detail}")
                
                try:
                    error_json = response.json()
                    print(f"   🔍 JSON ошибка: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                except:
                    pass
                    
                return False
                
            elif response.status_code == 422:
                print(f"   ❌ ОШИБКА 422 - Ошибка валидации")
                error_detail = response.text
                print(f"   📝 Детали ошибки: {error_detail}")
                
                try:
                    error_json = response.json()
                    print(f"   🔍 JSON ошибка: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                except:
                    pass
                    
                return False
                
            elif response.status_code == 500:
                print(f"   ❌ КРИТИЧЕСКАЯ ОШИБКА 500 - Внутренняя ошибка сервера")
                error_detail = response.text
                print(f"   📝 Детали ошибки: {error_detail}")
                
                try:
                    error_json = response.json()
                    print(f"   🔍 JSON ошибка: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                except:
                    pass
                    
                return False
            else:
                print(f"   ❌ Неожиданный статус код: {response.status_code}")
                print(f"   📝 Ответ: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ ТАЙМАУТ: Запрос превысил 30 секунд")
            return False
        except Exception as e:
            print(f"   ❌ Исключение при тестировании квартального маршрута: {e}")
            return False
    
    def test_different_cities_and_dates(self):
        """Тестирование с различными городами и датами для поиска паттернов"""
        print(f"\n🌍 ТЕСТИРОВАНИЕ РАЗЛИЧНЫХ ГОРОДОВ И ДАТ...")
        
        test_cases = [
            {"date": "2025-08-24", "city": "Кишинев"},
            {"date": "2025-08-24", "city": "Москва"},
            {"date": "2025-08-24", "city": "Киев"},
            {"date": "2025-01-15", "city": "Кишинев"},
            {"date": "2025-12-31", "city": "Кишинев"},
        ]
        
        results = {
            "daily": [],
            "monthly": [],
            "quarterly": []
        }
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   📋 Тест-кейс {i}/{len(test_cases)}: {test_case['date']} - {test_case['city']}")
            
            # Тестируем дневной маршрут
            daily_result = self.test_daily_route(test_case['date'], test_case['city'])
            results["daily"].append({"test_case": test_case, "success": daily_result})
            
            # Тестируем месячный маршрут
            monthly_result = self.test_monthly_route(test_case['date'], test_case['city'])
            results["monthly"].append({"test_case": test_case, "success": monthly_result})
            
            # Тестируем квартальный маршрут
            quarterly_result = self.test_quarterly_route(test_case['date'], test_case['city'])
            results["quarterly"].append({"test_case": test_case, "success": quarterly_result})
        
        # Анализ результатов
        print(f"\n📊 АНАЛИЗ РЕЗУЛЬТАТОВ:")
        
        for route_type, route_results in results.items():
            successful = sum(1 for r in route_results if r["success"])
            total = len(route_results)
            success_rate = (successful / total) * 100 if total > 0 else 0
            
            print(f"   {route_type.upper()}: {successful}/{total} успешных ({success_rate:.1f}%)")
            
            # Показываем неудачные случаи
            failed_cases = [r for r in route_results if not r["success"]]
            if failed_cases:
                print(f"      ❌ Неудачные случаи:")
                for case in failed_cases:
                    tc = case["test_case"]
                    print(f"         - {tc['date']} / {tc['city']}")
        
        return results
    
    def run_comprehensive_test(self):
        """Запуск комплексного тестирования"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Диагностика ошибок планетарного маршрута")
        print("=" * 80)
        
        # Аутентификация
        if not self.authenticate():
            print("❌ Не удалось аутентифицироваться. Тестирование прервано.")
            return False
        
        # Основные тесты с указанными в review request параметрами
        print(f"\n🎯 ОСНОВНЫЕ ТЕСТЫ (из review request):")
        
        # 1. Дневной маршрут для сравнения
        daily_success = self.test_daily_route("2025-08-24", "Кишинев")
        
        # 2. Месячный маршрут (КРИТИЧЕСКИЙ)
        monthly_success = self.test_monthly_route("2025-08-24", "Кишинев")
        
        # 3. Квартальный маршрут (КРИТИЧЕСКИЙ)
        quarterly_success = self.test_quarterly_route("2025-08-24", "Кишинев")
        
        # 4. Тестирование с различными параметрами
        pattern_results = self.test_different_cities_and_dates()
        
        # Финальный отчет
        print(f"\n" + "=" * 80)
        print(f"🎯 ФИНАЛЬНЫЙ ОТЧЕТ:")
        print(f"   📅 Дневной маршрут: {'✅ РАБОТАЕТ' if daily_success else '❌ НЕ РАБОТАЕТ'}")
        print(f"   🗓️ Месячный маршрут: {'✅ РАБОТАЕТ' if monthly_success else '❌ НЕ РАБОТАЕТ'}")
        print(f"   📆 Квартальный маршрут: {'✅ РАБОТАЕТ' if quarterly_success else '❌ НЕ РАБОТАЕТ'}")
        
        # Определяем критичность проблемы
        critical_issues = []
        if not monthly_success:
            critical_issues.append("Месячный планетарный маршрут")
        if not quarterly_success:
            critical_issues.append("Квартальный планетарный маршрут")
        
        if critical_issues:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ:")
            for issue in critical_issues:
                print(f"   ❌ {issue}")
        else:
            print(f"\n✅ Все планетарные маршруты работают корректно!")
        
        return len(critical_issues) == 0

def main():
    """Главная функция"""
    tester = PlanetaryRouteTestSuite()
    success = tester.run_comprehensive_test()
    
    if success:
        print(f"\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
        sys.exit(0)
    else:
        print(f"\n💥 ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ОШИБКИ")
        sys.exit(1)

if __name__ == "__main__":
    main()