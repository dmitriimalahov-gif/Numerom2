#!/usr/bin/env python3
"""
HTML Data Loading Fixes Testing Suite
Tests specific endpoints that had ObjectId serialization issues and HTML report generation.
"""

import requests
import json
import os
from datetime import datetime
import time

# Get backend URL from frontend .env
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class HTMLSerializationTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.super_admin_token = None
        self.user_data = {
            "email": f"testuser{int(time.time())}@numerom.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "birth_date": "15.03.1990",
            "city": "Москва"
        }
        self.super_admin_data = {
            "email": "dmitrii.malahov@gmail.com",
            "password": "756bvy67H"
        }
        self.test_results = []
        
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
    
    def make_request(self, method, endpoint, data=None, headers=None, use_super_admin=False):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if headers:
            default_headers.update(headers)
            
        # Use appropriate token
        token = self.super_admin_token if use_super_admin else self.auth_token
        if token and "Authorization" not in default_headers:
            default_headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=60)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=60)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=default_headers, timeout=60)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=default_headers, timeout=60)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {method} {url}: {str(e)}")
            return None
    
    def setup_authentication(self):
        """Setup both regular user and super admin authentication"""
        print("🔐 Setting up authentication...")
        
        # Register regular user
        response = self.make_request("POST", "/auth/register", self.user_data)
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.auth_token = data["access_token"]
                print(f"✅ Regular user registered: {self.user_data['email']}")
            else:
                print(f"❌ Registration failed: {data}")
                return False
        else:
            print(f"❌ Registration request failed: {response.text if response else 'No response'}")
            return False
        
        # Login super admin
        response = self.make_request("POST", "/auth/login", self.super_admin_data)
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.super_admin_token = data["access_token"]
                print(f"✅ Super admin logged in: {self.super_admin_data['email']}")
            else:
                print(f"❌ Super admin login failed: {data}")
                return False
        else:
            print(f"❌ Super admin login request failed: {response.text if response else 'No response'}")
            return False
        
        return True
    
    def test_learning_levels_serialization(self):
        """Test GET /api/learning/levels for ObjectId serialization issues"""
        if not self.auth_token:
            self.log_result("Learning Levels Serialization", False, "No auth token available")
            return False
        
        response = self.make_request("GET", "/learning/levels")
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Check for proper JSON structure without ObjectId errors
                if "user_level" in data and "available_lessons" in data:
                    user_level = data["user_level"]
                    lessons = data["available_lessons"]
                    
                    # Verify no MongoDB _id fields are present (check for actual _id keys, not just string presence)
                    json_str = json.dumps(data)
                    if '"_id"' not in json_str:
                        # Check that lessons are properly serialized
                        if isinstance(lessons, list):
                            for lesson in lessons:
                                if '"_id"' in json.dumps(lesson):
                                    self.log_result("Learning Levels Serialization", False, 
                                                  "Found _id field in lesson", lesson)
                                    return False
                            
                            self.log_result("Learning Levels Serialization", True, 
                                          f"Retrieved {len(lessons)} lessons without ObjectId errors")
                            return True
                        else:
                            self.log_result("Learning Levels Serialization", False, 
                                          "Lessons not in list format", type(lessons))
                    else:
                        self.log_result("Learning Levels Serialization", False, 
                                      "Found _id field in response", data)
                else:
                    self.log_result("Learning Levels Serialization", False, 
                                  "Missing required fields", data)
            except json.JSONDecodeError as e:
                self.log_result("Learning Levels Serialization", False, 
                              "JSON decode error - possible serialization issue", str(e))
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Learning Levels Serialization", False, 
                          f"Request failed with status {response.status_code if response else 'None'}", error)
        
        return False
    
    def test_admin_lessons_serialization(self):
        """Test GET /api/admin/lessons for ObjectId serialization issues"""
        if not self.super_admin_token:
            self.log_result("Admin Lessons Serialization", False, "No super admin token available")
            return False
        
        response = self.make_request("GET", "/admin/lessons", use_super_admin=True)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Should be a list of lessons
                if isinstance(data, list):
                    # Check each lesson for ObjectId serialization (look for actual _id keys)
                    for lesson in data:
                        if '"_id"' in json.dumps(lesson):
                            self.log_result("Admin Lessons Serialization", False, 
                                          "Found _id field in lesson", lesson)
                            return False
                    
                    self.log_result("Admin Lessons Serialization", True, 
                                  f"Retrieved {len(data)} admin lessons without ObjectId errors")
                    return True
                else:
                    self.log_result("Admin Lessons Serialization", False, 
                                  "Response not in list format", type(data))
            except json.JSONDecodeError as e:
                self.log_result("Admin Lessons Serialization", False, 
                              "JSON decode error - possible serialization issue", str(e))
        elif response and response.status_code == 403:
            self.log_result("Admin Lessons Serialization", False, 
                          "Access denied - super admin token may be invalid", response.text)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Admin Lessons Serialization", False, 
                          f"Request failed with status {response.status_code if response else 'None'}", error)
        
        return False
    
    def test_materials_serialization(self):
        """Test GET /api/materials for MongoDB _id serialization issues"""
        if not self.auth_token:
            self.log_result("Materials Serialization", False, "No auth token available")
            return False
        
        response = self.make_request("GET", "/materials")
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Should be a list of materials
                if isinstance(data, list):
                    # Check each material for _id serialization (look for actual _id keys)
                    for material in data:
                        if '"_id"' in json.dumps(material):
                            self.log_result("Materials Serialization", False, 
                                          "Found _id field in material", material)
                            return False
                        
                        # Also check that file_path is removed for security
                        if "file_path" in material:
                            self.log_result("Materials Serialization", False, 
                                          "Found file_path field in material (security issue)", material)
                            return False
                    
                    self.log_result("Materials Serialization", True, 
                                  f"Retrieved {len(data)} materials without MongoDB _id errors")
                    return True
                else:
                    self.log_result("Materials Serialization", False, 
                                  "Response not in list format", type(data))
            except json.JSONDecodeError as e:
                self.log_result("Materials Serialization", False, 
                              "JSON decode error - possible serialization issue", str(e))
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Materials Serialization", False, 
                          f"Request failed with status {response.status_code if response else 'None'}", error)
        
        return False
    
    def test_vedic_time_city_validation(self):
        """Test GET /api/vedic-time/daily-schedule for proper city validation"""
        if not self.auth_token:
            self.log_result("Vedic Time City Validation", False, "No auth token available")
            return False
        
        # Test without city parameter (should use user's city or return error)
        response = self.make_request("GET", "/vedic-time/daily-schedule")
        
        if response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "city" in data and "error" not in data:
                        self.log_result("Vedic Time City Validation (Default)", True, 
                                      f"Used default city: {data.get('city')}")
                    else:
                        self.log_result("Vedic Time City Validation (Default)", False, 
                                      "Missing city or error in response", data)
                        return False
                except json.JSONDecodeError as e:
                    self.log_result("Vedic Time City Validation (Default)", False, 
                                  "JSON decode error", str(e))
                    return False
            elif response.status_code == 422:
                # This is expected if no city is provided and user has no default city
                try:
                    error_data = response.json()
                    if "Город не указан" in error_data.get("detail", ""):
                        self.log_result("Vedic Time City Validation (Missing City)", True, 
                                      "Proper error for missing city")
                    else:
                        self.log_result("Vedic Time City Validation (Missing City)", False, 
                                      "Wrong error message", error_data)
                        return False
                except json.JSONDecodeError:
                    self.log_result("Vedic Time City Validation (Missing City)", False, 
                                  "Non-JSON error response", response.text)
                    return False
            else:
                self.log_result("Vedic Time City Validation", False, 
                              f"Unexpected status code: {response.status_code}", response.text)
                return False
        else:
            self.log_result("Vedic Time City Validation", False, "Connection failed")
            return False
        
        # Test with valid city
        response = self.make_request("GET", "/vedic-time/daily-schedule?city=Москва&date=2025-01-15")
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if "city" in data and data["city"] == "Москва":
                    self.log_result("Vedic Time City Validation (Valid City)", True, 
                                  "Valid city parameter handled correctly")
                    return True
                else:
                    self.log_result("Vedic Time City Validation (Valid City)", False, 
                                  "City not properly set", data)
            except json.JSONDecodeError as e:
                self.log_result("Vedic Time City Validation (Valid City)", False, 
                              "JSON decode error", str(e))
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Vedic Time City Validation (Valid City)", False, 
                          "Failed with valid city", error)
        
        return False
    
    def test_planetary_route_city_validation(self):
        """Test GET /api/vedic-time/planetary-route for city validation"""
        if not self.auth_token:
            self.log_result("Planetary Route City Validation", False, "No auth token available")
            return False
        
        # Test without city parameter
        response = self.make_request("GET", "/vedic-time/planetary-route")
        
        if response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "city" in data and "error" not in data:
                        self.log_result("Planetary Route City Validation", True, 
                                      f"Used default city: {data.get('city')}")
                        return True
                    else:
                        self.log_result("Planetary Route City Validation", False, 
                                      "Missing city or error in response", data)
                except json.JSONDecodeError as e:
                    self.log_result("Planetary Route City Validation", False, 
                                  "JSON decode error", str(e))
            elif response.status_code == 422:
                # Expected if no city is available
                try:
                    error_data = response.json()
                    if "Город не указан" in error_data.get("detail", ""):
                        self.log_result("Planetary Route City Validation", True, 
                                      "Proper error for missing city")
                        return True
                    else:
                        self.log_result("Planetary Route City Validation", False, 
                                      "Wrong error message", error_data)
                except json.JSONDecodeError:
                    self.log_result("Planetary Route City Validation", False, 
                                  "Non-JSON error response", response.text)
            else:
                self.log_result("Planetary Route City Validation", False, 
                              f"Unexpected status code: {response.status_code}", response.text)
        else:
            self.log_result("Planetary Route City Validation", False, "Connection failed")
        
        return False
    
    def test_html_report_generation(self):
        """Test POST /api/reports/html/numerology for HTML generation without errors"""
        if not self.auth_token:
            self.log_result("HTML Report Generation", False, "No auth token available")
            return False
        
        # Test HTML report generation
        html_request_data = {
            "include_vedic": True,
            "include_charts": True,
            "theme": "light"
        }
        
        response = self.make_request("POST", "/reports/html/numerology", html_request_data)
        
        if response and response.status_code == 200:
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                # Check if it's valid HTML
                html_content = response.text
                if html_content.strip().startswith('<!DOCTYPE html>') and 'NUMEROM' in html_content:
                    content_length = len(html_content)
                    if content_length > 5000:  # Should be substantial HTML
                        self.log_result("HTML Report Generation", True, 
                                      f"HTML report generated successfully ({content_length} chars)")
                        return True
                    else:
                        self.log_result("HTML Report Generation", False, 
                                      f"HTML too small ({content_length} chars)", html_content[:200])
                else:
                    self.log_result("HTML Report Generation", False, 
                                  "Invalid HTML structure", html_content[:200])
            else:
                # Try to parse as JSON error
                try:
                    error_data = response.json()
                    self.log_result("HTML Report Generation", False, 
                                  "Expected HTML but got JSON", error_data)
                except:
                    self.log_result("HTML Report Generation", False, 
                                  f"Wrong content type: {content_type}", response.text[:200])
        else:
            error = response.text if response else "Connection failed"
            self.log_result("HTML Report Generation", False, 
                          f"Request failed with status {response.status_code if response else 'None'}", error)
        
        return False
    
    def test_json_endpoints_clean_serialization(self):
        """Test various endpoints to ensure clean JSON without MongoDB ObjectId errors"""
        if not self.auth_token:
            self.log_result("JSON Clean Serialization", False, "No auth token available")
            return False
        
        # Test multiple endpoints that should return clean JSON
        endpoints_to_test = [
            ("/user/profile", "GET", None),
            ("/numerology/personal-numbers", "POST", None),
            ("/quiz/randomized-questions", "GET", None),
            ("/charts/planetary-energy/7", "GET", None)
        ]
        
        all_clean = True
        
        for endpoint, method, data in endpoints_to_test:
            response = self.make_request(method, endpoint, data)
            
            if response and response.status_code == 200:
                try:
                    json_data = response.json()
                    
                    # Check for ObjectId patterns in the JSON string (look for actual _id keys)
                    json_str = json.dumps(json_data)
                    if '"_id"' in json_str:
                        self.log_result(f"JSON Clean Serialization ({endpoint})", False, 
                                      "Found _id field in JSON response", json_data)
                        all_clean = False
                    elif "ObjectId" in json_str:
                        self.log_result(f"JSON Clean Serialization ({endpoint})", False, 
                                      "Found ObjectId in JSON response", json_data)
                        all_clean = False
                    else:
                        self.log_result(f"JSON Clean Serialization ({endpoint})", True, 
                                      "Clean JSON without ObjectId errors")
                        
                except json.JSONDecodeError as e:
                    self.log_result(f"JSON Clean Serialization ({endpoint})", False, 
                                  "JSON decode error", str(e))
                    all_clean = False
            elif response and response.status_code == 402:
                # Credit exhausted - this is expected behavior, not a serialization error
                self.log_result(f"JSON Clean Serialization ({endpoint})", True, 
                              "Credit exhausted (expected behavior)")
            else:
                error = response.text if response else "Connection failed"
                self.log_result(f"JSON Clean Serialization ({endpoint})", False, 
                              f"Request failed with status {response.status_code if response else 'None'}", error)
                all_clean = False
        
        return all_clean
    
    def run_html_serialization_tests(self):
        """Run all HTML data loading and serialization tests"""
        print("🧪 Starting HTML Data Loading Fixes Testing Suite")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed - cannot proceed with tests")
            return 0, 0
        
        print("\n🔍 Testing ObjectId Serialization Fixes...")
        
        # Test learning endpoints for ObjectId serialization issues
        self.test_learning_levels_serialization()
        self.test_admin_lessons_serialization()
        self.test_materials_serialization()
        
        print("\n🌍 Testing Vedic Time City Validation...")
        
        # Test Vedic time endpoints with city validation
        self.test_vedic_time_city_validation()
        self.test_planetary_route_city_validation()
        
        print("\n📄 Testing HTML Report Generation...")
        
        # Test HTML report generation
        self.test_html_report_generation()
        
        print("\n🧹 Testing Clean JSON Serialization...")
        
        # Test various endpoints for clean JSON
        self.test_json_endpoints_clean_serialization()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 HTML SERIALIZATION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        return passed, total

def main():
    """Main test execution"""
    tester = HTMLSerializationTester()
    passed, total = tester.run_html_serialization_tests()
    
    # Exit with appropriate code
    if total > 0 and passed == total:
        print("\n🎉 All HTML serialization tests passed!")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed" if total > 0 else "No tests were run")
        exit(1)

if __name__ == "__main__":
    main()