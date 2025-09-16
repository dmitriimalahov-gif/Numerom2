#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ВХОДА И ПРАВ ДОСТУПА
Authentication and Access Rights Testing Suite for NUMEROM
"""

import requests
import json
import uuid
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class AuthAccessTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.super_admin_token = None
        self.regular_user_token = None
        self.test_results = []
        
        # Super admin credentials from review request
        self.super_admin_creds = {
            "email": "dmitrii.malahov@gmail.com",
            "password": "756bvy67H"
        }
        
        # Test user credentials
        self.test_user_creds = {
            "email": f"testuser_{uuid.uuid4().hex[:8]}@test.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "birth_date": "01.01.1990",
            "city": "Москва"
        }
        
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
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if details and not success:
            print(f"   Details: {details}")
        print()
    
    def make_request(self, method, endpoint, data=None, headers=None, auth_token=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if auth_token:
            default_headers["Authorization"] = f"Bearer {auth_token}"
        
        if headers:
            default_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=default_headers, timeout=30)
            else:
                return None, f"Unsupported method: {method}"
            
            return response, None
        except requests.exceptions.RequestException as e:
            return None, str(e)
    
    def test_super_admin_login(self):
        """1. ТЕСТ СУПЕР АДМИНИСТРАТОРА"""
        print("=" * 60)
        print("1. ТЕСТ СУПЕР АДМИНИСТРАТОРА")
        print("=" * 60)
        
        # Test super admin login
        response, error = self.make_request("POST", "/auth/login", self.super_admin_creds)
        
        if error:
            self.log_result("Super Admin Login", False, f"Request failed: {error}")
            return False
        
        if response.status_code != 200:
            self.log_result("Super Admin Login", False, 
                          f"Login failed with status {response.status_code}", 
                          response.text)
            return False
        
        try:
            login_data = response.json()
            self.super_admin_token = login_data.get("access_token")
            user_info = login_data.get("user", {})
            
            # Check if login successful
            if not self.super_admin_token:
                self.log_result("Super Admin Login", False, "No access token received")
                return False
            
            # Check is_super_admin = true
            is_super_admin = user_info.get("is_super_admin", False)
            if not is_super_admin:
                self.log_result("Super Admin Rights Check", False, 
                              f"is_super_admin = {is_super_admin}, expected True")
                return False
            
            self.log_result("Super Admin Login", True, 
                          f"Successfully logged in as {user_info.get('email')} with super admin rights")
            
            # Test access to admin endpoints
            self.test_super_admin_endpoints()
            return True
            
        except json.JSONDecodeError:
            self.log_result("Super Admin Login", False, "Invalid JSON response", response.text)
            return False
    
    def test_super_admin_endpoints(self):
        """Test super admin access to admin endpoints"""
        admin_endpoints = [
            ("/admin/users", "GET", "Admin Users List"),
            ("/admin/materials", "GET", "Admin Materials List"),
            ("/admin/upload-video", "POST", "Admin Video Upload")
        ]
        
        for endpoint, method, description in admin_endpoints:
            if method == "POST" and "upload-video" in endpoint:
                # For video upload, we'll test with a mock file
                files = {'file': ('test.mp4', b'mock video content', 'video/mp4')}
                try:
                    url = f"{self.base_url}{endpoint}"
                    headers = {"Authorization": f"Bearer {self.super_admin_token}"}
                    response = requests.post(url, files=files, headers=headers, timeout=30)
                except Exception as e:
                    self.log_result(f"Super Admin Access - {description}", False, 
                                  f"Request failed: {str(e)}")
                    continue
            else:
                response, error = self.make_request(method, endpoint, auth_token=self.super_admin_token)
                if error:
                    self.log_result(f"Super Admin Access - {description}", False, 
                                  f"Request failed: {error}")
                    continue
            
            if response.status_code == 200:
                self.log_result(f"Super Admin Access - {description}", True, 
                              f"Successfully accessed {endpoint}")
            elif response.status_code == 403:
                self.log_result(f"Super Admin Access - {description}", False, 
                              f"Access denied (403) to {endpoint}")
            else:
                self.log_result(f"Super Admin Access - {description}", False, 
                              f"Unexpected status {response.status_code} for {endpoint}")
    
    def test_regular_user_registration_and_login(self):
        """2. ТЕСТ ОБЫЧНОГО ПОЛЬЗОВАТЕЛЯ"""
        print("=" * 60)
        print("2. ТЕСТ ОБЫЧНОГО ПОЛЬЗОВАТЕЛЯ")
        print("=" * 60)
        
        # Register new user
        response, error = self.make_request("POST", "/auth/register", self.test_user_creds)
        
        if error:
            self.log_result("Regular User Registration", False, f"Request failed: {error}")
            return False
        
        if response.status_code != 200:
            self.log_result("Regular User Registration", False, 
                          f"Registration failed with status {response.status_code}", 
                          response.text)
            return False
        
        try:
            reg_data = response.json()
            self.regular_user_token = reg_data.get("access_token")
            user_info = reg_data.get("user", {})
            
            # Check registration success
            if not self.regular_user_token:
                self.log_result("Regular User Registration", False, "No access token received")
                return False
            
            # Check is_super_admin = false or absent
            is_super_admin = user_info.get("is_super_admin", False)
            if is_super_admin:
                self.log_result("Regular User Rights Check", False, 
                              f"is_super_admin = {is_super_admin}, expected False")
                return False
            
            self.log_result("Regular User Registration", True, 
                          f"Successfully registered user {user_info.get('email')} without admin rights")
            
            # Test regular user access
            self.test_regular_user_access()
            return True
            
        except json.JSONDecodeError:
            self.log_result("Regular User Registration", False, "Invalid JSON response", response.text)
            return False
    
    def test_regular_user_access(self):
        """Test regular user access to endpoints"""
        # Test access to regular endpoints
        regular_endpoints = [
            ("/user/profile", "GET", "User Profile"),
            ("/numerology/personal-numbers", "POST", "Personal Numbers")
        ]
        
        for endpoint, method, description in regular_endpoints:
            data = None
            if "numerology" in endpoint:
                data = {"birth_date": "15.03.1990"}
            
            response, error = self.make_request(method, endpoint, data=data, auth_token=self.regular_user_token)
            
            if error:
                self.log_result(f"Regular User Access - {description}", False, 
                              f"Request failed: {error}")
                continue
            
            if response.status_code in [200, 402]:  # 402 = insufficient credits is OK
                self.log_result(f"Regular User Access - {description}", True, 
                              f"Successfully accessed {endpoint} (status: {response.status_code})")
            else:
                self.log_result(f"Regular User Access - {description}", False, 
                              f"Unexpected status {response.status_code} for {endpoint}")
        
        # Test NO ACCESS to admin endpoints
        admin_endpoints = [
            ("/admin/users", "GET", "Admin Users List"),
            ("/admin/materials", "GET", "Admin Materials List")
        ]
        
        for endpoint, method, description in admin_endpoints:
            response, error = self.make_request(method, endpoint, auth_token=self.regular_user_token)
            
            if error:
                self.log_result(f"Regular User Admin Block - {description}", False, 
                              f"Request failed: {error}")
                continue
            
            if response.status_code == 403:
                self.log_result(f"Regular User Admin Block - {description}", True, 
                              f"Correctly blocked access to {endpoint} (403)")
            else:
                self.log_result(f"Regular User Admin Block - {description}", False, 
                              f"Should be blocked but got status {response.status_code} for {endpoint}")
    
    def test_security_scenarios(self):
        """3. ТЕСТ БЕЗОПАСНОСТИ"""
        print("=" * 60)
        print("3. ТЕСТ БЕЗОПАСНОСТИ")
        print("=" * 60)
        
        admin_endpoints = [
            ("/admin/users", "GET", "Admin Users"),
            ("/admin/materials", "GET", "Admin Materials")
        ]
        
        for endpoint, method, description in admin_endpoints:
            # Test without token
            response, error = self.make_request(method, endpoint)
            
            if error:
                self.log_result(f"Security - No Token - {description}", False, 
                              f"Request failed: {error}")
            elif response.status_code == 401:
                self.log_result(f"Security - No Token - {description}", True, 
                              f"Correctly rejected access without token (401)")
            else:
                self.log_result(f"Security - No Token - {description}", False, 
                              f"Should reject but got status {response.status_code}")
            
            # Test with invalid token
            response, error = self.make_request(method, endpoint, auth_token="invalid_token_123")
            
            if error:
                self.log_result(f"Security - Invalid Token - {description}", False, 
                              f"Request failed: {error}")
            elif response.status_code == 401:
                self.log_result(f"Security - Invalid Token - {description}", True, 
                              f"Correctly rejected invalid token (401)")
            else:
                self.log_result(f"Security - Invalid Token - {description}", False, 
                              f"Should reject but got status {response.status_code}")
    
    def run_all_tests(self):
        """Run all authentication and access tests"""
        print("🔐 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ВХОДА И ПРАВ ДОСТУПА")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print(f"Test started at: {datetime.now().isoformat()}")
        print()
        
        # Run all test scenarios
        self.test_super_admin_login()
        self.test_regular_user_registration_and_login()
        self.test_security_scenarios()
        
        # Summary
        print("=" * 80)
        print("ИТОГИ ТЕСТИРОВАНИЯ / TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Всего тестов / Total tests: {total_tests}")
        print(f"Пройдено / Passed: {passed_tests}")
        print(f"Провалено / Failed: {failed_tests}")
        print(f"Успешность / Success rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("ПРОВАЛИВШИЕСЯ ТЕСТЫ / FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['message']}")
        else:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО / ALL TESTS PASSED!")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = AuthAccessTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)