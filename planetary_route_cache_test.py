#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ: Проверка месячного/квартального планетарного маршрута
Testing planetary route caching fixes after coordinate caching implementation

Review Request Testing:
1. Monthly planetary route - should work fast (< 5 seconds) without timeouts
2. Quarterly planetary route - should work fast (< 10 seconds) without timeouts  
3. Test with different cities: Кишинев, Москва, Киев, Минск
4. Verify data structure and content
5. Ensure no more timeout errors occur

Super Admin: dmitrii.malahov@gmail.com / 756bvy67H
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

class PlanetaryRouteCacheTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        
    def log_test(self, test_name, status, details="", response_time=None):
        """Log test results with timing"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status_icon} {test_name}{time_info}: {details}")
        
    def authenticate_super_admin(self):
        """Authenticate super admin user"""
        print("\n🔐 АУТЕНТИФИКАЦИЯ СУПЕР АДМИНА")
        
        try:
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            })
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user', {})
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                user_info = f"User ID: {self.user_data.get('id')}, Credits: {self.user_data.get('credits_remaining')}, Super Admin: {self.user_data.get('is_super_admin')}"
                self.log_test("Super Admin Login", "PASS", user_info, response_time)
                return True
            else:
                self.log_test("Super Admin Login", "FAIL", f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Super Admin Login", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_monthly_planetary_route(self, city, date="2025-08-24"):
        """Test monthly planetary route endpoint"""
        print(f"\n📅 ТЕСТ МЕСЯЧНОГО ПЛАНЕТАРНОГО МАРШРУТА - {city}")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/vedic-time/planetary-route/monthly", params={
                "date": date,
                "city": city
            })
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ['period', 'start_date', 'end_date', 'city', 'total_days', 'daily_schedule']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(f"Monthly Route {city}", "FAIL", f"Missing fields: {missing_fields}", response_time)
                    return False
                
                # Check if response time is acceptable (< 5 seconds)
                if response_time > 5.0:
                    self.log_test(f"Monthly Route {city}", "FAIL", f"Response too slow: {response_time:.2f}s > 5s limit", response_time)
                    return False
                
                # Verify daily schedule content
                daily_schedule = data.get('daily_schedule', [])
                if len(daily_schedule) < 25:  # Should have ~30 days
                    self.log_test(f"Monthly Route {city}", "FAIL", f"Insufficient days: {len(daily_schedule)} < 25", response_time)
                    return False
                
                # Check first day structure
                if daily_schedule:
                    first_day = daily_schedule[0]
                    day_required_fields = ['date', 'ruling_planet', 'recommendations']
                    day_missing_fields = [field for field in day_required_fields if field not in first_day]
                    
                    if day_missing_fields:
                        self.log_test(f"Monthly Route {city}", "FAIL", f"Day missing fields: {day_missing_fields}", response_time)
                        return False
                    
                    # Check if recommendations has best_hours
                    recommendations = first_day.get('recommendations', {})
                    if 'best_hours' not in recommendations:
                        self.log_test(f"Monthly Route {city}", "FAIL", f"Missing best_hours in recommendations", response_time)
                        return False
                
                success_details = f"✅ {len(daily_schedule)} days, Period: {data.get('period')}, City: {data.get('city')}"
                self.log_test(f"Monthly Route {city}", "PASS", success_details, response_time)
                return True
                
            else:
                error_details = f"Status: {response.status_code}"
                if response.status_code == 408 or "timeout" in response.text.lower():
                    error_details += " - TIMEOUT ERROR (критическая проблема!)"
                self.log_test(f"Monthly Route {city}", "FAIL", error_details, response_time)
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(f"Monthly Route {city}", "FAIL", "REQUEST TIMEOUT - критическая проблема!")
            return False
        except Exception as e:
            self.log_test(f"Monthly Route {city}", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_quarterly_planetary_route(self, city, date="2025-08-24"):
        """Test quarterly planetary route endpoint"""
        print(f"\n📊 ТЕСТ КВАРТАЛЬНОГО ПЛАНЕТАРНОГО МАРШРУТА - {city}")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/vedic-time/planetary-route/quarterly", params={
                "date": date,
                "city": city
            })
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ['period', 'start_date', 'end_date', 'city', 'total_weeks', 'weekly_schedule']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(f"Quarterly Route {city}", "FAIL", f"Missing fields: {missing_fields}", response_time)
                    return False
                
                # Check if response time is acceptable (< 10 seconds)
                if response_time > 10.0:
                    self.log_test(f"Quarterly Route {city}", "FAIL", f"Response too slow: {response_time:.2f}s > 10s limit", response_time)
                    return False
                
                # Verify weekly schedule content
                weekly_schedule = data.get('weekly_schedule', [])
                if len(weekly_schedule) < 10:  # Should have ~13 weeks
                    self.log_test(f"Quarterly Route {city}", "FAIL", f"Insufficient weeks: {len(weekly_schedule)} < 10", response_time)
                    return False
                
                # Check first week structure
                if weekly_schedule:
                    first_week = weekly_schedule[0]
                    week_required_fields = ['week_number', 'start_date', 'end_date', 'days']
                    week_missing_fields = [field for field in week_required_fields if field not in first_week]
                    
                    if week_missing_fields:
                        self.log_test(f"Quarterly Route {city}", "FAIL", f"Week missing fields: {week_missing_fields}", response_time)
                        return False
                    
                    # Check days in first week
                    days = first_week.get('days', [])
                    if len(days) < 5:  # Should have 7 days per week
                        self.log_test(f"Quarterly Route {city}", "FAIL", f"Insufficient days in week: {len(days)} < 5", response_time)
                        return False
                
                success_details = f"✅ {len(weekly_schedule)} weeks, Period: {data.get('period')}, City: {data.get('city')}"
                self.log_test(f"Quarterly Route {city}", "PASS", success_details, response_time)
                return True
                
            else:
                error_details = f"Status: {response.status_code}"
                if response.status_code == 408 or "timeout" in response.text.lower():
                    error_details += " - TIMEOUT ERROR (критическая проблема!)"
                self.log_test(f"Quarterly Route {city}", "FAIL", error_details, response_time)
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(f"Quarterly Route {city}", "FAIL", "REQUEST TIMEOUT - критическая проблема!")
            return False
        except Exception as e:
            self.log_test(f"Quarterly Route {city}", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_daily_route_baseline(self, city, date="2025-08-24"):
        """Test basic daily route as baseline"""
        print(f"\n🌅 БАЗОВЫЙ ТЕСТ ДНЕВНОГО МАРШРУТА - {city}")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/vedic-time/planetary-route", params={
                "date": date,
                "city": city
            })
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['date', 'city', 'daily_ruling_planet', 'best_activity_hours']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(f"Daily Route {city}", "FAIL", f"Missing fields: {missing_fields}", response_time)
                    return False
                
                success_details = f"✅ City: {data.get('city')}, Planet: {data.get('daily_ruling_planet')}"
                self.log_test(f"Daily Route {city}", "PASS", success_details, response_time)
                return True
            else:
                self.log_test(f"Daily Route {city}", "FAIL", f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"Daily Route {city}", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive planetary route cache testing"""
        print("🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ ПЛАНЕТАРНОГО МАРШРУТА")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate_super_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось аутентифицироваться")
            return False
        
        # Test cities as specified in review request
        test_cities = ["Кишинев", "Москва", "Киев", "Минск"]
        test_date = "2025-08-24"
        
        all_tests_passed = True
        
        # Step 2: Test daily routes first (baseline)
        print("\n" + "="*50)
        print("БАЗОВОЕ ТЕСТИРОВАНИЕ ДНЕВНЫХ МАРШРУТОВ")
        print("="*50)
        
        for city in test_cities:
            if not self.test_daily_route_baseline(city, test_date):
                all_tests_passed = False
        
        # Step 3: Test monthly routes
        print("\n" + "="*50)
        print("ТЕСТИРОВАНИЕ МЕСЯЧНЫХ МАРШРУТОВ (< 5 секунд)")
        print("="*50)
        
        for city in test_cities:
            if not self.test_monthly_planetary_route(city, test_date):
                all_tests_passed = False
        
        # Step 4: Test quarterly routes
        print("\n" + "="*50)
        print("ТЕСТИРОВАНИЕ КВАРТАЛЬНЫХ МАРШРУТОВ (< 10 секунд)")
        print("="*50)
        
        for city in test_cities:
            if not self.test_quarterly_planetary_route(city, test_date):
                all_tests_passed = False
        
        # Summary
        print("\n" + "="*80)
        print("ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("="*80)
        
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        total_tests = len(self.test_results)
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {passed_tests}")
        print(f"Неудачных: {total_tests - passed_tests}")
        print(f"Процент успеха: {(passed_tests/total_tests)*100:.1f}%")
        
        # Critical issues check
        timeout_issues = [r for r in self.test_results if 'timeout' in r['details'].lower() or 'TIMEOUT' in r['details']]
        slow_responses = [r for r in self.test_results if r.get('response_time', 0) > 10]
        
        if timeout_issues:
            print(f"\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ С ТАЙМАУТАМИ: {len(timeout_issues)}")
            for issue in timeout_issues:
                print(f"   - {issue['test']}: {issue['details']}")
        
        if slow_responses:
            print(f"\n⚠️ МЕДЛЕННЫЕ ОТВЕТЫ (>10s): {len(slow_responses)}")
            for slow in slow_responses:
                print(f"   - {slow['test']}: {slow['response_time']:.2f}s")
        
        if all_tests_passed and not timeout_issues:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО! Кеширование координат работает корректно.")
        else:
            print("\n❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ! Требуется дополнительная диагностика.")
        
        return all_tests_passed

def main():
    """Main test execution"""
    tester = PlanetaryRouteCacheTester()
    
    try:
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка тестирования: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()