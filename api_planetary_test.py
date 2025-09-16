#!/usr/bin/env python3
"""
API endpoint test for planetary strength calculation
Testing the review request requirements via the actual API
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://numerology-fix.preview.emergentagent.com') + '/api'

def test_api_endpoint():
    """Test the API endpoint with the super admin user"""
    print("🚀 Testing Planetary Strength API Endpoint")
    print("=" * 70)
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 70)
    
    test_results = []
    
    def log_result(test_name, success, message="", details=None):
        result = {"test": test_name, "success": success, "message": message, "details": details}
        test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def make_request(method, endpoint, data=None, headers=None):
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if headers:
            default_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {method} {url}: {str(e)}")
            return None
    
    # Login as super admin (has unlimited credits)
    login_data = {
        "email": "dmitrii.malahov@gmail.com",
        "password": "756bvy67H"
    }
    
    response = make_request("POST", "/auth/login", login_data)
    
    if not response or response.status_code != 200:
        log_result("Super Admin Login", False, "Failed to login as super admin", 
                  response.text if response else "Connection failed")
        return 0, 1
    
    login_result = response.json()
    auth_token = login_result.get("access_token")
    
    if not auth_token:
        log_result("Super Admin Login", False, "No access token received", login_result)
        return 0, 1
    
    log_result("Super Admin Login", True, "Successfully logged in as super admin")
    
    # Test the personal numbers endpoint with the specific birth date
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test with birth date 10.01.1982 as specified in review request
    test_data = {"birth_date": "10.01.1982"}  # Pass birth_date in request body
    response = make_request("POST", "/numerology/personal-numbers", test_data, headers)
    
    if not response or response.status_code != 200:
        log_result("API Endpoint Test", False, "Failed to call personal numbers API", 
                  response.text if response else "Connection failed")
        return 1, 2
    
    data = response.json()
    log_result("API Endpoint Test", True, "Successfully called personal numbers API")
    
    # Test 1: Check that only 7 planets are present (no Rahu/Ketu)
    planetary_strength = data.get("planetary_strength", {})
    expected_planets = ['Солнце', 'Луна', 'Марс', 'Меркурий', 'Юпитер', 'Венера', 'Сатурн']
    forbidden_planets = ['Раху', 'Кету']
    
    # Verify all expected planets are present
    missing_planets = [planet for planet in expected_planets if planet not in planetary_strength]
    if missing_planets:
        log_result("API 7 Planets Test", False, f"Missing planets: {missing_planets}", planetary_strength)
    else:
        # Verify forbidden planets are not present
        forbidden_found = [planet for planet in forbidden_planets if planet in planetary_strength]
        if forbidden_found:
            log_result("API 7 Planets Test", False, f"Forbidden planets found: {forbidden_found}", planetary_strength)
        else:
            # Verify exactly 7 planets
            if len(planetary_strength) != 7:
                log_result("API 7 Planets Test", False, f"Expected 7 planets, got {len(planetary_strength)}", planetary_strength)
            else:
                log_result("API 7 Planets Test", True, f"Exactly 7 planets present: {list(planetary_strength.keys())}")
    
    # Test 2: Check weekday field is present
    birth_weekday = data.get("birth_weekday", "")
    if birth_weekday:
        log_result("API Birth Weekday Test", True, f"Birth weekday present: {birth_weekday}")
    else:
        log_result("API Birth Weekday Test", False, "Birth weekday missing", data)
    
    # Test 3: Check calculation formula results
    # For 10.01.1982: 1001 * 1982 = 1983982, digits [1, 9, 8, 3, 9, 8, 2]
    expected_values = [1, 9, 8, 3, 9, 8, 2]
    planet_order = ['Солнце', 'Луна', 'Марс', 'Меркурий', 'Юпитер', 'Венера', 'Сатурн']
    actual_values = []
    
    for planet in planet_order:
        if planet in planetary_strength:
            actual_values.append(planetary_strength[planet])
    
    if actual_values == expected_values:
        log_result("API Calculation Formula Test", True, 
                  f"Values correctly distributed: {actual_values}")
    else:
        log_result("API Calculation Formula Test", False, 
                  f"Expected {expected_values}, got {actual_values}", planetary_strength)
    
    # Test 4: Check response structure
    required_fields = ["soul_number", "mind_number", "destiny_number", "helping_mind_number", 
                      "wisdom_number", "ruling_number", "planetary_strength", "birth_weekday"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        log_result("API Response Structure Test", False, f"Missing fields: {missing_fields}", list(data.keys()))
    else:
        log_result("API Response Structure Test", True, "All required fields present")
    
    # Print detailed API response
    print("\n" + "=" * 70)
    print("📊 API RESPONSE DETAILS")
    print("=" * 70)
    print(f"Birth Weekday: {birth_weekday}")
    print(f"Planetary Strength: {planetary_strength}")
    if "calculation_details" in data:
        print(f"Calculation Details: {data['calculation_details']}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 API TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for result in test_results if result["success"])
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Show failed tests
    failed_tests = [result for result in test_results if not result["success"]]
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"  - {test['test']}: {test['message']}")
    else:
        print("\n🎉 All API tests passed!")
    
    return passed, total

if __name__ == "__main__":
    passed, total = test_api_endpoint()
    
    if passed == total:
        print("\n✅ All API tests passed!")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        exit(1)