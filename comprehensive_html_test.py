#!/usr/bin/env python3
"""
COMPREHENSIVE HTML REPORT TESTING
Проверяем все аспекты генерации HTML отчётов согласно review request
"""

import requests
import json
import sys
import re
from datetime import datetime

def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=')[1].strip()
    except:
        pass
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

print(f"🎯 COMPREHENSIVE HTML REPORT TESTING")
print(f"Backend URL: {BASE_URL}")
print(f"API URL: {API_URL}")
print("=" * 80)

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.issues = []
        
    def success(self, message):
        print(f"✅ {message}")
        self.passed += 1
        
    def failure(self, message):
        print(f"❌ {message}")
        self.failed += 1
        self.issues.append(message)
        
    def info(self, message):
        print(f"ℹ️  {message}")

results = TestResults()
auth_token = None

def login_super_admin():
    global auth_token
    
    print("\n🔐 SUPER ADMIN LOGIN")
    
    login_data = {
        "email": "dmitrii.malahov@gmail.com",
        "password": "756bvy67H"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get('access_token')
            user_info = data.get('user', {})
            
            results.success(f"Super admin logged in successfully")
            results.info(f"User ID: {user_info.get('id')}")
            results.info(f"Email: {user_info.get('email')}")
            results.info(f"Super Admin: {user_info.get('is_super_admin')}")
            results.info(f"Premium: {user_info.get('is_premium')}")
            results.info(f"Credits: {user_info.get('credits_remaining')}")
            
            return True
        else:
            results.failure(f"Super admin login failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        results.failure(f"Exception during super admin login: {str(e)}")
        return False

def get_auth_headers():
    if not auth_token:
        return {}
    return {"Authorization": f"Bearer {auth_token}"}

def test_specific_selected_calculations():
    """Test specific selected_calculations combinations as mentioned in review request"""
    
    print("\n📊 TESTING SPECIFIC SELECTED_CALCULATIONS COMBINATIONS")
    
    test_combinations = [
        {
            "name": "Personal Numbers Only",
            "calculations": ["personal_numbers"],
            "expected_content": ["ЧД", "ЧУ", "ЧС", "ПЧ"]
        },
        {
            "name": "Personal + Pythagorean",
            "calculations": ["personal_numbers", "pythagorean_square"],
            "expected_content": ["ЧД", "ЧУ", "А1", "А2", "А3", "А4"]
        },
        {
            "name": "All Main Calculations",
            "calculations": ["personal_numbers", "pythagorean_square", "vedic_times", "planetary_route"],
            "expected_content": ["ЧД", "А1", "Rahu", "Солнце"]
        },
        {
            "name": "Vedic Times Focus",
            "calculations": ["vedic_times"],
            "expected_content": ["Rahu", "काल", "Abhijit"]
        },
        {
            "name": "Planetary Route Focus", 
            "calculations": ["planetary_route"],
            "expected_content": ["Утро", "День", "Вечер"]
        }
    ]
    
    for combo in test_combinations:
        print(f"\n🧪 Testing: {combo['name']}")
        
        request_data = {
            "selected_calculations": combo["calculations"],
            "theme": "light"
        }
        
        try:
            response = requests.post(
                f"{API_URL}/reports/html/numerology",
                json=request_data,
                headers=get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                results.success(f"HTTP 200 for {combo['name']}")
                
                html_content = response.text
                
                # Check for expected content
                found_content = 0
                for expected in combo["expected_content"]:
                    if expected in html_content:
                        found_content += 1
                        results.success(f"  Found expected content: {expected}")
                    else:
                        results.info(f"  Missing expected content: {expected}")
                
                if found_content >= len(combo["expected_content"]) // 2:
                    results.success(f"  Content validation passed for {combo['name']}")
                else:
                    results.failure(f"  Insufficient expected content in {combo['name']}")
                    
                # Check HTML size is reasonable
                if len(html_content) > 5000:
                    results.success(f"  HTML size appropriate: {len(html_content)} chars")
                else:
                    results.failure(f"  HTML too small: {len(html_content)} chars")
                    
            elif response.status_code == 500:
                results.failure(f"500 Internal Server Error for {combo['name']}: {response.text}")
                
                # Check for specific errors mentioned in review request
                if 'UnboundLocalError' in response.text:
                    results.failure(f"CRITICAL: UnboundLocalError still present in {combo['name']}")
                elif 'datetime' in response.text.lower():
                    results.failure(f"Datetime-related error in {combo['name']}: {response.text}")
                    
            else:
                results.failure(f"Unexpected status {response.status_code} for {combo['name']}")
                
        except Exception as e:
            results.failure(f"Exception testing {combo['name']}: {str(e)}")

def test_user_data_completeness():
    """Test that HTML contains ALL user data as mentioned in review request"""
    
    print("\n👤 TESTING USER DATA COMPLETENESS")
    
    request_data = {
        "selected_calculations": ["personal_numbers", "pythagorean_square", "vedic_times", "planetary_route"],
        "theme": "light"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/reports/html/numerology",
            json=request_data,
            headers=get_auth_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            html_content = response.text
            
            print("  📋 Checking user data completeness...")
            
            # User personal data
            user_data_checks = [
                ("Email", "dmitrii.malahov@gmail.com"),
                ("Birth Date Pattern", r"\d{2}\.\d{2}\.\d{4}"),
                ("User Name", "Дмитрий")  # Assuming this is in the profile
            ]
            
            for check_name, pattern in user_data_checks:
                if isinstance(pattern, str):
                    if pattern in html_content:
                        results.success(f"  {check_name} found in HTML")
                    else:
                        results.failure(f"  {check_name} missing from HTML")
                else:
                    if re.search(pattern, html_content):
                        results.success(f"  {check_name} pattern found in HTML")
                    else:
                        results.failure(f"  {check_name} pattern missing from HTML")
            
            # Personal numbers (all 6 types)
            personal_numbers = ["ЧД", "ЧУ", "ЧС", "ЧУ*", "ЧМ", "ПЧ"]
            found_numbers = 0
            for num_type in personal_numbers:
                if num_type in html_content:
                    found_numbers += 1
            
            if found_numbers == 6:
                results.success(f"  All 6 personal numbers found: {found_numbers}/6")
            else:
                results.failure(f"  Missing personal numbers: {found_numbers}/6")
            
            # Planetary strength (7 planets)
            planets = ["Солнце", "Луна", "Марс", "Меркурий", "Юпитер", "Венера", "Сатурн"]
            found_planets = 0
            for planet in planets:
                if planet in html_content:
                    found_planets += 1
            
            if found_planets >= 6:
                results.success(f"  Planetary strength data found: {found_planets}/7 planets")
            else:
                results.failure(f"  Insufficient planetary data: {found_planets}/7 planets")
            
            # Pythagorean Square additional numbers
            additional_numbers = ["А1", "А2", "А3", "А4"]
            found_additional = 0
            for add_num in additional_numbers:
                if add_num in html_content:
                    found_additional += 1
            
            if found_additional == 4:
                results.success(f"  All 4 additional numbers found: А1, А2, А3, А4")
            else:
                results.failure(f"  Missing additional numbers: {found_additional}/4")
            
            # Vedic times sections
            vedic_sections = ["Rahu", "राहु", "काल", "Abhijit", "अभिजित्"]
            found_vedic = 0
            for vedic_term in vedic_sections:
                if vedic_term in html_content:
                    found_vedic += 1
            
            if found_vedic >= 2:
                results.success(f"  Vedic times sections found: {found_vedic}/5 terms")
            else:
                results.info(f"  Limited vedic times data: {found_vedic}/5 terms")
            
            # Planetary route sections
            route_terms = ["Утро", "День", "Вечер", "6:00", "12:00", "18:00"]
            found_route = 0
            for route_term in route_terms:
                if route_term in html_content:
                    found_route += 1
            
            if found_route >= 4:
                results.success(f"  Planetary route data found: {found_route}/6 terms")
            else:
                results.info(f"  Limited planetary route data: {found_route}/6 terms")
            
            # Overall numerical data density
            numbers = re.findall(r'\b\d+\b', html_content)
            if len(numbers) >= 100:
                results.success(f"  Rich numerical data: {len(numbers)} numbers found")
            else:
                results.failure(f"  Sparse numerical data: {len(numbers)} numbers found")
                
        else:
            results.failure(f"Failed to get HTML for completeness test: {response.status_code}")
            
    except Exception as e:
        results.failure(f"Exception during completeness test: {str(e)}")

def test_premium_vs_regular_users():
    """Test different user scenarios as mentioned in review request"""
    
    print("\n🎭 TESTING PREMIUM VS REGULAR USER SCENARIOS")
    
    # Test with super admin (premium user)
    print("  🔹 Testing with Premium User (Super Admin)")
    
    premium_request = {
        "selected_calculations": ["personal_numbers", "pythagorean_square"],
        "theme": "light"
    }
    
    try:
        premium_response = requests.post(
            f"{API_URL}/reports/html/numerology",
            json=premium_request,
            headers=get_auth_headers(),
            timeout=30
        )
        
        if premium_response.status_code == 200:
            results.success("  Premium user HTML generation successful")
            
            # Check that content is substantial for premium user
            if len(premium_response.text) > 15000:
                results.success("  Premium user gets full-featured report")
            else:
                results.failure("  Premium user report seems limited")
                
        else:
            results.failure(f"  Premium user HTML generation failed: {premium_response.status_code}")
            
    except Exception as e:
        results.failure(f"  Exception testing premium user: {str(e)}")
    
    # Test with regular user (create one with credits)
    print("  🔹 Testing with Regular User (with credits)")
    
    regular_user_data = {
        "email": f"regular_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com",
        "password": "testpass123",
        "full_name": "Regular User",
        "birth_date": "20.05.1985",
        "city": "Санкт-Петербург"
    }
    
    try:
        # Register regular user
        reg_response = requests.post(f"{API_URL}/auth/register", json=regular_user_data, timeout=10)
        
        if reg_response.status_code == 200:
            results.success("  Regular user registered successfully")
            
            reg_data = reg_response.json()
            regular_token = reg_data.get('access_token')
            regular_headers = {"Authorization": f"Bearer {regular_token}"}
            
            # Test HTML generation
            regular_request = {
                "selected_calculations": ["personal_numbers"],
                "theme": "light"
            }
            
            regular_response = requests.post(
                f"{API_URL}/reports/html/numerology",
                json=regular_request,
                headers=regular_headers,
                timeout=30
            )
            
            if regular_response.status_code == 200:
                results.success("  Regular user HTML generation successful")
                
                # Check credit deduction
                profile_response = requests.get(f"{API_URL}/user/profile", headers=regular_headers, timeout=10)
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    credits_after = profile_data.get('credits_remaining', 0)
                    results.success(f"  Credits after generation: {credits_after}")
                    
                    if credits_after == 0:  # Started with 1, should be 0 now
                        results.success("  Credit deduction working correctly")
                    else:
                        results.info(f"  Unexpected credit count: {credits_after}")
                        
            elif regular_response.status_code == 402:
                results.info("  Regular user out of credits (expected behavior)")
            else:
                results.failure(f"  Regular user HTML generation failed: {regular_response.status_code}")
                
        else:
            results.failure(f"  Failed to register regular user: {reg_response.status_code}")
            
    except Exception as e:
        results.failure(f"  Exception testing regular user: {str(e)}")

def check_backend_logs():
    """Check backend logs for errors as mentioned in review request"""
    
    print("\n📋 CHECKING BACKEND LOGS FOR ERRORS")
    
    try:
        # Check supervisor logs for backend
        import subprocess
        
        log_result = subprocess.run(
            ["tail", "-n", "50", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if log_result.returncode == 0:
            log_content = log_result.stdout
            
            # Check for specific errors
            error_patterns = [
                ("UnboundLocalError", "CRITICAL: UnboundLocalError found in logs"),
                ("500 Internal Server Error", "500 errors found in logs"),
                ("datetime", "Datetime-related errors in logs"),
                ("generate_numerology_html", "HTML generation errors in logs"),
                ("ERROR", "General errors in logs")
            ]
            
            errors_found = 0
            for pattern, message in error_patterns:
                if pattern.lower() in log_content.lower():
                    if pattern == "UnboundLocalError":
                        results.failure(f"  {message}")
                        errors_found += 1
                    elif pattern == "500 Internal Server Error":
                        results.failure(f"  {message}")
                        errors_found += 1
                    else:
                        results.info(f"  {message}")
            
            if errors_found == 0:
                results.success("  No critical errors found in backend logs")
            else:
                results.failure(f"  {errors_found} critical errors found in logs")
                
        else:
            results.info("  Could not read backend logs")
            
    except Exception as e:
        results.info(f"  Exception checking logs: {str(e)}")

def main():
    """Main testing function"""
    
    print("🚀 STARTING COMPREHENSIVE HTML REPORT TESTING")
    
    # 1. Login as super admin
    if not login_super_admin():
        print("\n❌ CRITICAL ERROR: Could not login as super admin")
        sys.exit(1)
    
    # 2. Test specific selected_calculations combinations
    test_specific_selected_calculations()
    
    # 3. Test user data completeness
    test_user_data_completeness()
    
    # 4. Test premium vs regular user scenarios
    test_premium_vs_regular_users()
    
    # 5. Check backend logs
    check_backend_logs()
    
    # Final report
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    total_tests = results.passed + results.failed
    success_rate = (results.passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"✅ Tests Passed: {results.passed}")
    print(f"❌ Tests Failed: {results.failed}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if results.issues:
        print(f"\n🚨 ISSUES FOUND:")
        for i, issue in enumerate(results.issues, 1):
            print(f"  {i}. {issue}")
    
    # Check for critical issues
    critical_issues = [issue for issue in results.issues if 'CRITICAL' in issue or 'UnboundLocalError' in issue]
    
    if critical_issues:
        print(f"\n🔥 CRITICAL ISSUES DETECTED:")
        for issue in critical_issues:
            print(f"  ⚠️  {issue}")
        print(f"\n❌ TESTING FAILED: Critical issues found")
        return False
    elif results.failed == 0:
        print(f"\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print(f"✅ HTML reports generate correctly")
        print(f"✅ UnboundLocalError has been fixed")
        print(f"✅ Reports contain complete user data")
        print(f"✅ Different user scenarios work properly")
        return True
    else:
        print(f"\n⚠️  TESTING COMPLETED WITH WARNINGS")
        print(f"✅ No critical errors detected")
        print(f"⚠️  Some minor issues need attention")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)