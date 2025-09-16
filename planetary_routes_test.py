#!/usr/bin/env python3
"""
NUMEROM Planetary Routes API Testing Suite
Tests new planetary route endpoints as requested in review:
1. GET /api/vedic-time/planetary-route (basic)
2. GET /api/vedic-time/planetary-route/monthly 
3. GET /api/vedic-time/planetary-route/quarterly
4. GET /api/vedic-time/daily-schedule (updated)
5. Credit deduction verification
6. City and date validation
7. Multiple cities testing (Moscow, St. Petersburg, New York)
"""

import requests
import json
import os
from datetime import datetime, timedelta
import time

BACKEND_URL = "http://localhost:8001/api"

class PlanetaryRouteTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        # Use super admin credentials as specified in review request
        self.super_admin_data = {
            "email": "dmitrii.malahov@gmail.com",
            "password": "756bvy67H"
        }
        self.test_results = []
        self.cities_to_test = ["Москва", "Санкт-Петербург", "Нью-Йорк"]
        
    def log_result(self, test_name, success, message="", details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def make_request(self, method, endpoint, data=None, headers=None, params=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if headers:
            default_headers.update(headers)
            
        if self.auth_token:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
    
    def login_super_admin(self):
        """Login with super admin credentials"""
        print("\n🔐 LOGGING IN AS SUPER ADMIN...")
        
        response = self.make_request("POST", "/auth/login", self.super_admin_data)
        
        if response and response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            user_info = data.get("user", {})
            
            self.log_result(
                "Super Admin Login",
                True,
                f"Logged in successfully. Credits: {user_info.get('credits_remaining', 'N/A')}, Premium: {user_info.get('is_premium', False)}"
            )
            return True
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Super Admin Login", False, f"Login failed: {error_msg}")
            return False
    
    def get_user_credits(self):
        """Get current user credits"""
        response = self.make_request("GET", "/user/profile")
        if response and response.status_code == 200:
            return response.json().get("credits_remaining", 0)
        return None
    
    def test_basic_planetary_route(self):
        """Test basic planetary route endpoint"""
        print("\n🌟 TESTING BASIC PLANETARY ROUTE...")
        
        initial_credits = self.get_user_credits()
        
        response = self.make_request("GET", "/vedic-time/planetary-route")
        
        if response and response.status_code == 200:
            data = response.json()
            required_fields = [
                'date', 'city', 'personal_birth_date', 'daily_ruling_planet',
                'best_activity_hours', 'avoid_periods', 'favorable_period',
                'hourly_guide', 'daily_recommendations'
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                final_credits = self.get_user_credits()
                credit_deducted = initial_credits is not None and final_credits is not None and initial_credits > final_credits
                
                self.log_result(
                    "Basic Planetary Route",
                    True,
                    f"All required fields present. Credits deducted: {credit_deducted}",
                    f"Response keys: {list(data.keys())}"
                )
            else:
                self.log_result(
                    "Basic Planetary Route",
                    False,
                    f"Missing required fields: {missing_fields}",
                    f"Available fields: {list(data.keys())}"
                )
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Basic Planetary Route", False, f"Request failed: {error_msg}")
    
    def test_monthly_planetary_route(self):
        """Test monthly planetary route endpoint"""
        print("\n📅 TESTING MONTHLY PLANETARY ROUTE...")
        
        test_date = "2025-03-15"
        
        for city in self.cities_to_test:
            print(f"  Testing city: {city}")
            initial_credits = self.get_user_credits()
            
            params = {
                "date": test_date,
                "city": city
            }
            
            response = self.make_request("GET", "/vedic-time/planetary-route/monthly", params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                
                # Check for expected monthly route structure
                expected_fields = ['period', 'city', 'start_date', 'daily_routes']
                has_required_fields = any(field in data for field in expected_fields)
                
                final_credits = self.get_user_credits()
                credit_deducted = initial_credits is not None and final_credits is not None and initial_credits > final_credits
                
                self.log_result(
                    f"Monthly Route - {city}",
                    True,
                    f"Response received. Credits deducted: {credit_deducted}",
                    f"Response size: {len(str(data))} chars"
                )
            else:
                error_msg = response.json().get("detail", "Unknown error") if response else "Connection failed"
                self.log_result(f"Monthly Route - {city}", False, f"Request failed: {error_msg}")
    
    def test_quarterly_planetary_route(self):
        """Test quarterly planetary route endpoint"""
        print("\n📊 TESTING QUARTERLY PLANETARY ROUTE...")
        
        test_date = "2025-03-15"
        
        for city in self.cities_to_test:
            print(f"  Testing city: {city}")
            initial_credits = self.get_user_credits()
            
            params = {
                "date": test_date,
                "city": city
            }
            
            response = self.make_request("GET", "/vedic-time/planetary-route/quarterly", params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                
                # Check for expected quarterly route structure
                expected_fields = ['period', 'city', 'start_date', 'quarterly_overview']
                has_required_fields = any(field in data for field in expected_fields)
                
                final_credits = self.get_user_credits()
                credit_deducted = initial_credits is not None and final_credits is not None and initial_credits > final_credits
                
                self.log_result(
                    f"Quarterly Route - {city}",
                    True,
                    f"Response received. Credits deducted: {credit_deducted}",
                    f"Response size: {len(str(data))} chars"
                )
            else:
                error_msg = response.json().get("detail", "Unknown error") if response else "Connection failed"
                self.log_result(f"Quarterly Route - {city}", False, f"Request failed: {error_msg}")
    
    def test_vedic_daily_schedule(self):
        """Test updated vedic daily schedule endpoint"""
        print("\n🕐 TESTING VEDIC DAILY SCHEDULE...")
        
        test_date = "2025-03-15"
        
        for city in self.cities_to_test:
            print(f"  Testing city: {city}")
            initial_credits = self.get_user_credits()
            
            params = {
                "date": test_date,
                "city": city
            }
            
            response = self.make_request("GET", "/vedic-time/daily-schedule", params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                
                # Check for required vedic time fields
                required_fields = [
                    'city', 'weekday', 'sun_times', 'inauspicious_periods',
                    'auspicious_periods', 'planetary_hours', 'recommendations'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                # Check for specific periods
                inauspicious = data.get('inauspicious_periods', {})
                has_rahu_kaal = 'rahu_kaal' in inauspicious
                has_gulika_kaal = 'gulika_kaal' in inauspicious
                has_yamaghanta = 'yamaghanta' in inauspicious
                
                auspicious = data.get('auspicious_periods', {})
                has_abhijit = 'abhijit_muhurta' in auspicious
                
                final_credits = self.get_user_credits()
                credit_deducted = initial_credits is not None and final_credits is not None and initial_credits > final_credits
                
                if not missing_fields and has_rahu_kaal and has_gulika_kaal and has_yamaghanta and has_abhijit:
                    self.log_result(
                        f"Vedic Daily Schedule - {city}",
                        True,
                        f"All periods present. Credits deducted: {credit_deducted}",
                        f"Periods: Rahu Kaal, Gulika Kaal, Yamaghanta, Abhijit Muhurta"
                    )
                else:
                    self.log_result(
                        f"Vedic Daily Schedule - {city}",
                        False,
                        f"Missing fields: {missing_fields}. Missing periods: {not has_rahu_kaal and 'Rahu Kaal' or ''} {not has_gulika_kaal and 'Gulika Kaal' or ''} {not has_yamaghanta and 'Yamaghanta' or ''} {not has_abhijit and 'Abhijit' or ''}".strip()
                    )
            else:
                error_msg = response.json().get("detail", "Unknown error") if response else "Connection failed"
                self.log_result(f"Vedic Daily Schedule - {city}", False, f"Request failed: {error_msg}")
    
    def test_invalid_city_validation(self):
        """Test city validation with invalid cities"""
        print("\n🚫 TESTING CITY VALIDATION...")
        
        invalid_cities = ["InvalidCity123", "NonExistentPlace", ""]
        
        for invalid_city in invalid_cities:
            params = {
                "date": "2025-03-15",
                "city": invalid_city
            }
            
            response = self.make_request("GET", "/vedic-time/daily-schedule", params=params)
            
            if response and response.status_code in [400, 422]:
                self.log_result(
                    f"City Validation - '{invalid_city}'",
                    True,
                    f"Correctly rejected invalid city with status {response.status_code}"
                )
            else:
                self.log_result(
                    f"City Validation - '{invalid_city}'",
                    False,
                    f"Should have rejected invalid city but got status {response.status_code if response else 'None'}"
                )
    
    def test_invalid_date_validation(self):
        """Test date validation with invalid dates"""
        print("\n📅 TESTING DATE VALIDATION...")
        
        invalid_dates = ["invalid-date", "2025-13-45", "not-a-date", ""]
        
        for invalid_date in invalid_dates:
            params = {
                "date": invalid_date,
                "city": "Москва"
            }
            
            response = self.make_request("GET", "/vedic-time/daily-schedule", params=params)
            
            if response and response.status_code == 400:
                self.log_result(
                    f"Date Validation - '{invalid_date}'",
                    True,
                    f"Correctly rejected invalid date with status {response.status_code}"
                )
            else:
                self.log_result(
                    f"Date Validation - '{invalid_date}'",
                    False,
                    f"Should have rejected invalid date but got status {response.status_code if response else 'None'}"
                )
    
    def test_credit_deduction_verification(self):
        """Verify credit deduction works correctly for all endpoints"""
        print("\n💳 TESTING CREDIT DEDUCTION VERIFICATION...")
        
        # Test each endpoint and verify credits are deducted
        endpoints_to_test = [
            ("/vedic-time/planetary-route", "GET", None),
            ("/vedic-time/planetary-route/monthly", "GET", {"date": "2025-03-15", "city": "Москва"}),
            ("/vedic-time/planetary-route/quarterly", "GET", {"date": "2025-03-15", "city": "Москва"}),
            ("/vedic-time/daily-schedule", "GET", {"date": "2025-03-15", "city": "Москва"})
        ]
        
        for endpoint, method, params in endpoints_to_test:
            initial_credits = self.get_user_credits()
            
            if initial_credits is None:
                self.log_result(f"Credit Check - {endpoint}", False, "Could not get initial credits")
                continue
            
            response = self.make_request(method, endpoint, params=params)
            
            if response and response.status_code == 200:
                final_credits = self.get_user_credits()
                
                if final_credits is not None:
                    credit_deducted = initial_credits > final_credits
                    credits_diff = initial_credits - final_credits
                    
                    self.log_result(
                        f"Credit Deduction - {endpoint}",
                        credit_deducted,
                        f"Credits: {initial_credits} → {final_credits} (diff: {credits_diff})"
                    )
                else:
                    self.log_result(f"Credit Deduction - {endpoint}", False, "Could not get final credits")
            else:
                self.log_result(f"Credit Deduction - {endpoint}", False, "Endpoint request failed")
    
    def run_all_tests(self):
        """Run all planetary route tests"""
        print("🚀 STARTING PLANETARY ROUTES API TESTING SUITE")
        print("=" * 60)
        
        # Login first
        if not self.login_super_admin():
            print("❌ Cannot proceed without authentication")
            return 0, 1
        
        # Run all tests
        self.test_basic_planetary_route()
        self.test_monthly_planetary_route()
        self.test_quarterly_planetary_route()
        self.test_vedic_daily_schedule()
        self.test_invalid_city_validation()
        self.test_invalid_date_validation()
        self.test_credit_deduction_verification()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = PlanetaryRouteTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)