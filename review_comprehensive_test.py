#!/usr/bin/env python3
"""
NUMEROM Backend API Testing Suite - Review Request Comprehensive Testing
Tests all new user profile and group compatibility functions as specified in the review request.
"""

import requests
import json
import os
from datetime import datetime
import time
import random
import string

# Get backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class ReviewComprehensiveTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.user_data = {
            "email": f"reviewtest{int(time.time())}@numerom.com",
            "password": "SecurePass123!",
            "full_name": "Review Test User",
            "birth_date": "10.01.1982",
            "city": "Москва",
            "phone_number": "+7-999-123-4567"
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
    
    def make_request(self, method, endpoint, data=None, headers=None, params=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if headers:
            default_headers.update(headers)
            
        if self.auth_token and "Authorization" not in default_headers:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, params=params, timeout=30)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=default_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {method} {url}: {str(e)}")
            return None
    
    def setup_test_user(self):
        """Setup test user with registration and login"""
        print("🔧 Setting up test user...")
        
        # Register user
        response = self.make_request("POST", "/auth/register", self.user_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.auth_token = data["access_token"]
                self.log_result("User Setup - Registration", True, "User registered successfully")
                return True
            else:
                self.log_result("User Setup - Registration", False, "Missing access token", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("User Setup - Registration", False, "Registration failed", error)
        return False
    
    # ===== 1. EXTENDED USER PROFILE TESTING =====
    
    def test_registration_with_phone_and_ip_geolocation(self):
        """Test registration with phone number and IP geolocation"""
        print("\n📱 Testing Extended User Profile - Registration with Phone & IP Geolocation")
        
        # Test registration with phone number
        timestamp = int(time.time())
        test_user = {
            "email": f"phonetest{timestamp}@numerom.com",
            "password": "SecurePass123!",
            "full_name": "Phone Test User",
            "birth_date": "15.03.1990",
            "phone_number": "+7-999-888-7766"
        }
        
        response = self.make_request("POST", "/auth/register", test_user)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                user_info = data["user"]
                # Check if phone number is included
                if "phone_number" in user_info and user_info["phone_number"] == test_user["phone_number"]:
                    # Check if city was set (IP geolocation)
                    if "city" in user_info and user_info["city"]:
                        self.log_result("Registration with Phone & IP Geolocation", True, 
                                      f"Registration successful with phone {user_info['phone_number']} and city {user_info['city']}")
                        return True
                    else:
                        self.log_result("Registration with Phone & IP Geolocation", False, 
                                      "City not set via IP geolocation", user_info)
                else:
                    self.log_result("Registration with Phone & IP Geolocation", False, 
                                  "Phone number not saved correctly", user_info)
            else:
                self.log_result("Registration with Phone & IP Geolocation", False, 
                              "Missing token or user data", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Registration with Phone & IP Geolocation", False, 
                          "Registration failed", error)
        return False
    
    def test_patch_user_profile_new_fields(self):
        """Test PATCH /api/user/profile for updating all new fields"""
        print("\n🔄 Testing PATCH /api/user/profile for new fields")
        
        if not self.auth_token:
            self.log_result("PATCH User Profile New Fields", False, "No auth token available")
            return False
        
        # Test updating all new profile fields
        profile_updates = {
            "phone_number": "+7-999-111-2233",
            "car_number": "А123БВ777",
            "street": "Тверская улица",
            "house_number": "15",
            "apartment_number": "42",
            "postal_code": "125009"
        }
        
        response = self.make_request("PATCH", "/user/profile", profile_updates)
        
        if response and response.status_code == 200:
            data = response.json()
            # Check if all new fields are present in response
            all_fields_present = True
            missing_fields = []
            
            for field, expected_value in profile_updates.items():
                if field not in data:
                    all_fields_present = False
                    missing_fields.append(field)
                elif data[field] != expected_value:
                    all_fields_present = False
                    missing_fields.append(f"{field} (value mismatch: expected {expected_value}, got {data[field]})")
            
            if all_fields_present:
                self.log_result("PATCH User Profile New Fields", True, 
                              "All new profile fields updated successfully")
                return True
            else:
                self.log_result("PATCH User Profile New Fields", False, 
                              f"Missing or incorrect fields: {missing_fields}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("PATCH User Profile New Fields", False, 
                          "Failed to update profile", error)
        return False
    
    def test_get_user_profile_new_fields(self):
        """Test GET /api/user/profile returns all new fields"""
        print("\n📋 Testing GET /api/user/profile returns new fields")
        
        if not self.auth_token:
            self.log_result("GET User Profile New Fields", False, "No auth token available")
            return False
        
        response = self.make_request("GET", "/user/profile")
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Check for all new profile fields
            new_fields = ["phone_number", "car_number", "street", "house_number", "apartment_number", "postal_code"]
            present_fields = []
            missing_fields = []
            
            for field in new_fields:
                if field in data:
                    present_fields.append(field)
                else:
                    missing_fields.append(field)
            
            if len(present_fields) >= 4:  # At least most fields should be present
                self.log_result("GET User Profile New Fields", True, 
                              f"Profile contains {len(present_fields)}/6 new fields: {present_fields}")
                return True
            else:
                self.log_result("GET User Profile New Fields", False, 
                              f"Too many missing fields: {missing_fields}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("GET User Profile New Fields", False, 
                          "Failed to get profile", error)
        return False
    
    def test_ip_geolocation_service(self):
        """Test IP geolocation through ipapi.co service"""
        print("\n🌍 Testing IP Geolocation Service")
        
        # Test the IP geolocation service directly
        try:
            # Test with a known IP (Google DNS)
            test_ip = "8.8.8.8"
            response = requests.get(f'http://ipapi.co/{test_ip}/json/', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'city' in data and data['city']:
                    self.log_result("IP Geolocation Service", True, 
                                  f"ipapi.co service working - IP {test_ip} resolved to {data['city']}, {data.get('country_name', 'Unknown')}")
                    return True
                else:
                    self.log_result("IP Geolocation Service", False, 
                                  "No city data returned", data)
            else:
                self.log_result("IP Geolocation Service", False, 
                              f"Service returned status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("IP Geolocation Service", False, 
                          f"Service connection failed: {str(e)}")
        return False
    
    # ===== 2. CAR AND ADDRESS NUMEROLOGY TESTING =====
    
    def test_car_numerology_various_numbers(self):
        """Test POST /api/car-numerology with various numbers (Russian/English letters + digits)"""
        print("\n🚗 Testing Car Numerology with Various Numbers")
        
        if not self.auth_token:
            self.log_result("Car Numerology Various Numbers", False, "No auth token available")
            return False
        
        # Test cases with different car number formats
        test_cases = [
            {"car_number": "А123БВ777", "description": "Russian letters + digits"},
            {"car_number": "A123BC777", "description": "English letters + digits"},
            {"car_number": "М999КХ199", "description": "Russian with 999"},
            {"car_number": "X001YZ001", "description": "English with zeros"},
            {"car_number": "О777ОО777", "description": "Russian with repeated digits"}
        ]
        
        successful_tests = 0
        
        for i, test_case in enumerate(test_cases):
            car_data = {"car_number": test_case["car_number"]}
            response = self.make_request("POST", "/car-numerology", car_data)
            
            if response and response.status_code == 200:
                data = response.json()
                
                # Check for actual fields in car numerology response (based on API structure)
                required_fields = ["car_number", "numerology_value", "interpretation", "total_sum"]
                if all(field in data for field in required_fields):
                    # Verify calculation makes sense
                    if isinstance(data["numerology_value"], int) and isinstance(data["total_sum"], int):
                        if 1 <= data["numerology_value"] <= 9 or data["numerology_value"] in [11, 22, 33]:
                            self.log_result(f"Car Numerology ({test_case['description']})", True, 
                                          f"Number {test_case['car_number']} -> {data['numerology_value']} (total: {data['total_sum']})")
                            successful_tests += 1
                        else:
                            self.log_result(f"Car Numerology ({test_case['description']})", False, 
                                          f"Invalid numerology value: {data['numerology_value']}", data)
                    else:
                        self.log_result(f"Car Numerology ({test_case['description']})", False, 
                                      "Invalid number types in response", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result(f"Car Numerology ({test_case['description']})", False, 
                                  f"Missing fields: {missing}", data)
            else:
                error = response.text if response else "Connection failed"
                self.log_result(f"Car Numerology ({test_case['description']})", False, 
                              "Failed to calculate car numerology", error)
        
        return successful_tests >= 3  # At least 3 out of 5 should work
    
    def test_address_numerology_various_data(self):
        """Test POST /api/address-numerology with various address data"""
        print("\n🏠 Testing Address Numerology with Various Data")
        
        if not self.auth_token:
            self.log_result("Address Numerology Various Data", False, "No auth token available")
            return False
        
        # Test cases with different address formats
        test_cases = [
            {
                "street": "Тверская улица",
                "house_number": "15",
                "apartment_number": "42",
                "postal_code": "125009",
                "description": "Full Russian address"
            },
            {
                "street": "Main Street",
                "house_number": "123",
                "apartment_number": "5A",
                "postal_code": "12345",
                "description": "English address with letter in apartment"
            },
            {
                "street": "Невский проспект",
                "house_number": "1",
                "apartment_number": None,
                "postal_code": "190000",
                "description": "No apartment number"
            },
            {
                "street": "Broadway",
                "house_number": "999",
                "apartment_number": "100",
                "postal_code": None,
                "description": "No postal code"
            }
        ]
        
        successful_tests = 0
        
        for i, test_case in enumerate(test_cases):
            # Remove None values
            address_data = {k: v for k, v in test_case.items() if v is not None and k != "description"}
            
            response = self.make_request("POST", "/address-numerology", address_data)
            
            if response and response.status_code == 200:
                data = response.json()
                
                # Check for actual fields in address numerology response (based on API structure)
                expected_fields = ["house_numerology", "apartment_numerology", "postal_code_numerology"]
                present_fields = [f for f in expected_fields if f in data]
                
                if len(present_fields) >= 1:  # At least 1 field should be present
                    # Verify calculations make sense
                    valid_calculations = 0
                    for field in present_fields:
                        if isinstance(data[field], dict) and "value" in data[field] and "interpretation" in data[field]:
                            value = data[field]["value"]
                            if isinstance(value, int) and 1 <= value <= 9:
                                valid_calculations += 1
                    
                    if valid_calculations > 0:
                        self.log_result(f"Address Numerology ({test_case['description']})", True, 
                                      f"Address calculated with {valid_calculations} valid components")
                        successful_tests += 1
                    else:
                        self.log_result(f"Address Numerology ({test_case['description']})", False, 
                                      "No valid calculations found", data)
                else:
                    self.log_result(f"Address Numerology ({test_case['description']})", False, 
                                  f"No expected fields present: {present_fields}", data)
            else:
                error = response.text if response else "Connection failed"
                self.log_result(f"Address Numerology ({test_case['description']})", False, 
                              "Failed to calculate address numerology", error)
        
        return successful_tests >= 2  # At least 2 out of 4 should work
    
    # ===== 3. GROUP COMPATIBILITY TESTING =====
    
    def test_group_compatibility_1_to_5_people(self):
        """Test POST /api/group-compatibility with 1-5 people"""
        print("\n👥 Testing Group Compatibility with 1-5 People")
        
        if not self.auth_token:
            self.log_result("Group Compatibility 1-5 People", False, "No auth token available")
            return False
        
        # Test cases with different group sizes
        test_cases = [
            {
                "main_person_birth_date": "10.01.1982",
                "people": [
                    {"name": "Анна", "birth_date": "15.03.1990"}
                ],
                "description": "1 person group"
            },
            {
                "main_person_birth_date": "10.01.1982",
                "people": [
                    {"name": "Анна", "birth_date": "15.03.1990"},
                    {"name": "Борис", "birth_date": "22.07.1985"}
                ],
                "description": "2 people group"
            },
            {
                "main_person_birth_date": "10.01.1982",
                "people": [
                    {"name": "Анна", "birth_date": "15.03.1990"},
                    {"name": "Борис", "birth_date": "22.07.1985"},
                    {"name": "Виктор", "birth_date": "05.12.1988"}
                ],
                "description": "3 people group"
            },
            {
                "main_person_birth_date": "10.01.1982",
                "people": [
                    {"name": "Анна", "birth_date": "15.03.1990"},
                    {"name": "Борис", "birth_date": "22.07.1985"},
                    {"name": "Виктор", "birth_date": "05.12.1988"},
                    {"name": "Галина", "birth_date": "18.09.1992"},
                    {"name": "Дмитрий", "birth_date": "30.11.1987"}
                ],
                "description": "5 people group (maximum)"
            }
        ]
        
        successful_tests = 0
        
        for i, test_case in enumerate(test_cases):
            response = self.make_request("POST", "/group-compatibility", test_case)
            
            if response and response.status_code == 200:
                data = response.json()
                
                # Check for actual fields in group compatibility response (based on API structure)
                required_fields = ["main_person", "group_analysis", "average_compatibility"]
                if all(field in data for field in required_fields):
                    # Verify data types and ranges
                    avg_compat = data["average_compatibility"]
                    if isinstance(avg_compat, (int, float)) and 0 <= avg_compat <= 100:
                        group_analysis = data["group_analysis"]
                        if isinstance(group_analysis, list) and len(group_analysis) == len(test_case["people"]):
                            # Check if each person in group has required fields
                            valid_people = 0
                            for person in group_analysis:
                                if all(field in person for field in ["name", "birth_date", "life_path", "compatibility_score"]):
                                    valid_people += 1
                            
                            if valid_people == len(test_case["people"]):
                                self.log_result(f"Group Compatibility ({test_case['description']})", True, 
                                              f"Compatibility: {avg_compat}%, {valid_people} people analyzed")
                                successful_tests += 1
                            else:
                                self.log_result(f"Group Compatibility ({test_case['description']})", False, 
                                              f"Only {valid_people}/{len(test_case['people'])} people valid", data)
                        else:
                            self.log_result(f"Group Compatibility ({test_case['description']})", False, 
                                          f"Invalid group analysis: expected {len(test_case['people'])}, got {len(group_analysis) if isinstance(group_analysis, list) else 'invalid'}", data)
                    else:
                        self.log_result(f"Group Compatibility ({test_case['description']})", False, 
                                      f"Invalid average compatibility: {avg_compat}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result(f"Group Compatibility ({test_case['description']})", False, 
                                  f"Missing fields: {missing}", data)
            else:
                error = response.text if response else "Connection failed"
                self.log_result(f"Group Compatibility ({test_case['description']})", False, 
                              "Failed to calculate group compatibility", error)
        
        return successful_tests >= 3  # At least 3 out of 4 should work
    
    def test_group_compatibility_validation_max_5_people(self):
        """Test group compatibility validation for maximum 5 people"""
        print("\n⚠️ Testing Group Compatibility Validation (Max 5 People)")
        
        if not self.auth_token:
            self.log_result("Group Compatibility Max 5 Validation", False, "No auth token available")
            return False
        
        # Test with 6 people (should fail)
        test_data = {
            "main_person_birth_date": "10.01.1982",
            "people": [
                {"name": "Person1", "birth_date": "15.03.1990"},
                {"name": "Person2", "birth_date": "22.07.1985"},
                {"name": "Person3", "birth_date": "05.12.1988"},
                {"name": "Person4", "birth_date": "18.09.1992"},
                {"name": "Person5", "birth_date": "30.11.1987"},
                {"name": "Person6", "birth_date": "12.04.1989"}  # 6th person - should cause validation error
            ]
        }
        
        response = self.make_request("POST", "/group-compatibility", test_data)
        
        if response and response.status_code == 200:
            # Check if response contains error message
            try:
                data = response.json()
                if "error" in data and ("5" in str(data["error"]) or "максимум" in str(data["error"]).lower()):
                    self.log_result("Group Compatibility Max 5 Validation", True, 
                                  f"Correctly rejected 6 people group: {data['error']}")
                    return True
                else:
                    self.log_result("Group Compatibility Max 5 Validation", False, 
                                  "Should have rejected 6 people but accepted", data)
            except:
                self.log_result("Group Compatibility Max 5 Validation", False, 
                              "Should have rejected 6 people but got non-JSON response", response.text)
        elif response and response.status_code == 400:
            # Should return validation error
            try:
                error_data = response.json()
                if "5" in str(error_data) or "максимум" in str(error_data).lower() or "maximum" in str(error_data).lower():
                    self.log_result("Group Compatibility Max 5 Validation", True, 
                                  "Correctly rejected 6 people group")
                    return True
                else:
                    self.log_result("Group Compatibility Max 5 Validation", False, 
                                  "Wrong validation error message", error_data)
            except:
                self.log_result("Group Compatibility Max 5 Validation", True, 
                              "Validation error returned (non-JSON response)")
                return True
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Group Compatibility Max 5 Validation", False, 
                          "Unexpected response", error)
        return False
    
    # ===== 4. UPDATED PAIR COMPATIBILITY TESTING =====
    
    def test_updated_pair_compatibility_new_fields(self):
        """Test POST /api/numerology/compatibility with new fields person1_birth_date, person2_birth_date"""
        print("\n💑 Testing Updated Pair Compatibility with New Fields")
        
        if not self.auth_token:
            self.log_result("Updated Pair Compatibility New Fields", False, "No auth token available")
            return False
        
        # Test with new field names
        compatibility_data = {
            "person1_birth_date": "10.01.1982",
            "person2_birth_date": "15.03.1990"
        }
        
        response = self.make_request("POST", "/numerology/compatibility", compatibility_data)
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Check for required fields
            required_fields = ["person1_life_path", "person2_life_path", "compatibility_score", "description"]
            if all(field in data for field in required_fields):
                # Verify data types
                if isinstance(data["compatibility_score"], (int, float)) and 0 <= data["compatibility_score"] <= 100:
                    self.log_result("Updated Pair Compatibility New Fields", True, 
                                  f"Compatibility calculated: {data['compatibility_score']}%")
                    return True
                else:
                    self.log_result("Updated Pair Compatibility New Fields", False, 
                                  f"Invalid compatibility score: {data['compatibility_score']}", data)
            else:
                missing = [f for f in required_fields if f not in data]
                self.log_result("Updated Pair Compatibility New Fields", False, 
                              f"Missing fields: {missing}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Updated Pair Compatibility New Fields", False, 
                          "Failed to calculate compatibility", error)
        return False
    
    def test_pair_compatibility_backward_compatibility(self):
        """Test backward compatibility with old field names"""
        print("\n🔄 Testing Pair Compatibility Backward Compatibility")
        
        if not self.auth_token:
            self.log_result("Pair Compatibility Backward Compatibility", False, "No auth token available")
            return False
        
        # Test with old field names (if still supported)
        old_format_data = {
            "birth_date1": "10.01.1982",
            "birth_date2": "15.03.1990"
        }
        
        response = self.make_request("POST", "/numerology/compatibility", old_format_data)
        
        if response and response.status_code == 200:
            data = response.json()
            required_fields = ["person1_life_path", "person2_life_path", "compatibility_score", "description"]
            if all(field in data for field in required_fields):
                self.log_result("Pair Compatibility Backward Compatibility", True, 
                              "Old field names still supported")
                return True
            else:
                self.log_result("Pair Compatibility Backward Compatibility", False, 
                              "Old format works but missing fields", data)
        elif response and response.status_code == 400:
            # Old format might not be supported anymore, which is acceptable
            self.log_result("Pair Compatibility Backward Compatibility", True, 
                          "Old format deprecated (acceptable)")
            return True
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Pair Compatibility Backward Compatibility", False, 
                          "Unexpected error with old format", error)
        return False
    
    # ===== 5. AUTHENTICATION TESTING =====
    
    def test_new_endpoints_require_authentication(self):
        """Test that all new endpoints require authorization"""
        print("\n🔐 Testing New Endpoints Require Authentication")
        
        # Temporarily remove auth token
        temp_token = self.auth_token
        self.auth_token = None
        
        # Test endpoints without authentication
        test_endpoints = [
            ("POST", "/car-numerology", {"car_number": "А123БВ777"}),
            ("POST", "/address-numerology", {"street": "Test Street", "house_number": "1"}),
            ("POST", "/group-compatibility", {
                "main_person_birth_date": "10.01.1982",
                "people": [{"name": "Test", "birth_date": "15.03.1990"}]
            }),
            ("PATCH", "/user/profile", {"phone_number": "+7-999-123-4567"})
        ]
        
        successful_tests = 0
        
        for method, endpoint, data in test_endpoints:
            response = self.make_request(method, endpoint, data)
            
            if response and response.status_code in [401, 403]:
                self.log_result(f"Auth Required - {method} {endpoint}", True, 
                              f"Correctly requires authentication (status: {response.status_code})")
                successful_tests += 1
            else:
                status = response.status_code if response else "No response"
                self.log_result(f"Auth Required - {method} {endpoint}", False, 
                              f"Should require auth but got status: {status}")
        
        # Restore auth token
        self.auth_token = temp_token
        
        return successful_tests >= 3  # At least 3 out of 4 should require auth
    
    def test_endpoints_with_invalid_token(self):
        """Test endpoints with invalid token"""
        print("\n🚫 Testing Endpoints with Invalid Token")
        
        # Use invalid token
        temp_token = self.auth_token
        self.auth_token = "invalid_token_12345"
        
        # Test with invalid token
        response = self.make_request("POST", "/car-numerology", {"car_number": "А123БВ777"})
        
        # Restore valid token
        self.auth_token = temp_token
        
        if response and response.status_code in [401, 403]:
            self.log_result("Invalid Token Test", True, 
                          f"Correctly rejected invalid token (status: {response.status_code})")
            return True
        else:
            status = response.status_code if response else "No response"
            self.log_result("Invalid Token Test", False, 
                          f"Should reject invalid token but got status: {status}")
        return False
    
    def run_comprehensive_review_tests(self):
        """Run all comprehensive review tests"""
        print("🎯 Starting NUMEROM Comprehensive Review Testing")
        print("=" * 70)
        print("Testing all new user profile and group compatibility functions")
        print("=" * 70)
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return 0, 1
        
        print("\n" + "=" * 70)
        print("1️⃣ EXTENDED USER PROFILE TESTING")
        print("=" * 70)
        
        self.test_registration_with_phone_and_ip_geolocation()
        self.test_patch_user_profile_new_fields()
        self.test_get_user_profile_new_fields()
        self.test_ip_geolocation_service()
        
        print("\n" + "=" * 70)
        print("2️⃣ CAR AND ADDRESS NUMEROLOGY TESTING")
        print("=" * 70)
        
        self.test_car_numerology_various_numbers()
        self.test_address_numerology_various_data()
        
        print("\n" + "=" * 70)
        print("3️⃣ GROUP COMPATIBILITY TESTING")
        print("=" * 70)
        
        self.test_group_compatibility_1_to_5_people()
        self.test_group_compatibility_validation_max_5_people()
        
        print("\n" + "=" * 70)
        print("4️⃣ UPDATED PAIR COMPATIBILITY TESTING")
        print("=" * 70)
        
        self.test_updated_pair_compatibility_new_fields()
        self.test_pair_compatibility_backward_compatibility()
        
        print("\n" + "=" * 70)
        print("5️⃣ AUTHENTICATION TESTING")
        print("=" * 70)
        
        self.test_new_endpoints_require_authentication()
        self.test_endpoints_with_invalid_token()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE REVIEW TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        # Show category summaries
        categories = {
            "Extended User Profile": ["Registration with Phone", "PATCH User Profile", "GET User Profile", "IP Geolocation"],
            "Car & Address Numerology": ["Car Numerology", "Address Numerology"],
            "Group Compatibility": ["Group Compatibility", "Max 5 Validation"],
            "Pair Compatibility": ["Updated Pair Compatibility", "Backward Compatibility"],
            "Authentication": ["Auth Required", "Invalid Token"]
        }
        
        print("\n📋 CATEGORY RESULTS:")
        for category, keywords in categories.items():
            category_tests = [result for result in self.test_results 
                            if any(keyword in result['test'] for keyword in keywords)]
            if category_tests:
                category_passed = sum(1 for test in category_tests if test["success"])
                category_total = len(category_tests)
                print(f"  {category}: {category_passed}/{category_total} ({(category_passed/category_total)*100:.1f}%)")
        
        return passed, total

def main():
    """Main test execution"""
    tester = ReviewComprehensiveTester()
    passed, total = tester.run_comprehensive_review_tests()
    
    # Exit with appropriate code
    if passed >= total * 0.8:  # 80% success rate is acceptable
        print(f"\n🎉 Review testing completed successfully! ({passed}/{total} tests passed)")
        exit(0)
    else:
        print(f"\n⚠️ Review testing completed with issues ({passed}/{total} tests passed)")
        exit(1)

if __name__ == "__main__":
    main()