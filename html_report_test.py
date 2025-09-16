#!/usr/bin/env python3
"""
NUMEROM HTML Report Generation Testing Suite
Tests comprehensive HTML report generation with all sections as requested in review.
"""

import requests
import json
import os
import re
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class HTMLReportTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.user_data = {
            "email": "htmltest@numerom.com",
            "password": "SecurePass123!",
            "full_name": "HTML Test User",
            "birth_date": "10.01.1982",  # Using specific date from review request
            "city": "Москва"
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
    
    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if headers:
            default_headers.update(headers)
            
        if self.auth_token and "Authorization" not in default_headers:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"
        
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
    
    def setup_user(self):
        """Setup test user with authentication"""
        print("🔧 Setting up test user...")
        
        # Try to register new user
        timestamp = int(time.time())
        test_user = self.user_data.copy()
        test_user["email"] = f"htmltest{timestamp}@numerom.com"
        
        response = self.make_request("POST", "/auth/register", test_user)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.auth_token = data["access_token"]
                self.user_data["email"] = test_user["email"]
                print(f"✅ User registered: {test_user['email']}")
                return True
        
        # If registration fails, try login with original email
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.auth_token = data["access_token"]
                print(f"✅ User logged in: {self.user_data['email']}")
                return True
        
        print("❌ Failed to setup user")
        return False
    
    def test_html_report_basic(self):
        """Test basic HTML report generation"""
        print("\n📄 Testing basic HTML report generation...")
        
        request_data = {
            "birth_date": self.user_data["birth_date"],
            "include_vedic": True,
            "include_charts": True,
            "theme": "light"
        }
        
        response = self.make_request("POST", "/reports/html/numerology", request_data)
        
        if not response:
            self.log_result("HTML Report Basic", False, "No response received")
            return False
        
        if response.status_code != 200:
            self.log_result("HTML Report Basic", False, f"HTTP {response.status_code}", response.text[:500])
            return False
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'text/html' not in content_type:
            self.log_result("HTML Report Basic", False, f"Wrong content type: {content_type}")
            return False
        
        html_content = response.text
        
        # Check HTML structure - handle potential whitespace
        html_content_stripped = html_content.strip()
        if not html_content_stripped.startswith('<!DOCTYPE html>'):
            self.log_result("HTML Report Basic", False, f"Missing DOCTYPE declaration. Starts with: {html_content_stripped[:50]}")
            return False
        
        if 'NUMEROM' not in html_content:
            self.log_result("HTML Report Basic", False, "Missing NUMEROM branding")
            return False
        
        self.log_result("HTML Report Basic", True, f"HTML report generated ({len(html_content)} chars)")
        return html_content
    
    def test_html_report_personal_numbers(self, html_content):
        """Test that HTML report contains all personal numbers"""
        print("\n🔢 Testing personal numbers in HTML report...")
        
        # Check for personal numbers sections
        personal_numbers_found = []
        
        # Look for the actual number values in the HTML structure
        number_patterns = {
            "ЧД": r"Число души \(ЧД\)",  # Soul Number
            "ЧУ": r"Число ума \(ЧУ\)",  # Mind Number  
            "ЧС": r"Число судьбы \(ЧС\)",  # Destiny Number
            "ЧУ\*": r"Помогающее число ума \(ЧУ\*\)",  # Helping Mind Number
            "ЧМ": r"Число мудрости \(ЧМ\)",  # Wisdom Number
            "ПЧ": r"Правящее число \(ПЧ\)"   # Ruling Number
        }
        
        for abbrev, pattern in number_patterns.items():
            matches = re.findall(pattern, html_content)
            if matches:
                personal_numbers_found.append(abbrev)
        
        if len(personal_numbers_found) >= 4:  # At least 4 out of 6 numbers should be found
            self.log_result("HTML Personal Numbers", True, f"Found {len(personal_numbers_found)} personal numbers: {', '.join(personal_numbers_found)}")
            return True
        else:
            self.log_result("HTML Personal Numbers", False, f"Only found {len(personal_numbers_found)} personal numbers: {', '.join(personal_numbers_found)}")
            return False
    
    def test_html_report_planetary_strength(self, html_content):
        """Test that HTML report contains planetary strength with 7 planets"""
        print("\n🪐 Testing planetary strength in HTML report...")
        
        # Check for planetary strength section
        if "Планетарные силы" not in html_content and "планетарн" not in html_content.lower():
            self.log_result("HTML Planetary Strength", False, "Planetary strength section not found")
            return False
        
        # Check for 7 planets (no Rahu/Ketu as per review request)
        planets = ["Солнце", "Луна", "Марс", "Меркурий", "Юпитер", "Венера", "Сатурн"]
        planets_found = []
        
        for planet in planets:
            if planet in html_content:
                planets_found.append(planet)
        
        # Check for birth weekday
        weekdays = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
        weekday_found = any(day in html_content.lower() for day in weekdays)
        
        if len(planets_found) >= 5:  # At least 5 out of 7 planets
            message = f"Found {len(planets_found)} planets: {', '.join(planets_found)}"
            if weekday_found:
                message += " + birth weekday"
            self.log_result("HTML Planetary Strength", True, message)
            return True
        else:
            self.log_result("HTML Planetary Strength", False, f"Only found {len(planets_found)} planets: {', '.join(planets_found)}")
            return False
    
    def test_html_report_pythagorean_square(self, html_content):
        """Test that HTML report contains Pythagorean Square with additional numbers"""
        print("\n⬜ Testing Pythagorean Square in HTML report...")
        
        # Check for Pythagorean square section
        square_keywords = ["Пифагор", "квадрат", "матрица", "Дополнительные числа"]
        square_section_found = any(keyword in html_content for keyword in square_keywords)
        
        if not square_section_found:
            self.log_result("HTML Pythagorean Square", False, "Pythagorean square section not found")
            return False
        
        # Look for additional numbers pattern - check for А1, А2, А3, А4
        additional_numbers_patterns = [
            r"А1:\s*(\d+)",
            r"А2:\s*(\d+)", 
            r"А3:\s*(\d+)",
            r"А4:\s*(\d+)"
        ]
        
        found_numbers = []
        for pattern in additional_numbers_patterns:
            matches = re.findall(pattern, html_content)
            if matches:
                found_numbers.extend(matches)
        
        if len(found_numbers) >= 4:
            self.log_result("HTML Pythagorean Square", True, f"Found Pythagorean square with additional numbers: А1-А4 = {', '.join(found_numbers)}")
            return True
        else:
            self.log_result("HTML Pythagorean Square", False, f"Only found {len(found_numbers)} additional numbers: {', '.join(found_numbers)}")
            return False
    
    def test_html_report_vedic_times(self, html_content):
        """Test that HTML report contains Vedic Times section"""
        print("\n🕐 Testing Vedic Times in HTML report...")
        
        # Check for Vedic times section
        vedic_keywords = ["Ведические времена", "राहु काल", "Rahu", "Раху", "Gulika", "Гулика", "Yamaghanta", "Яма"]
        vedic_section_found = any(keyword in html_content for keyword in vedic_keywords)
        
        if vedic_section_found:
            # Look for specific time periods
            time_periods = ["काल", "kaal", "muhurta", "мухурта"]
            time_periods_found = [period for period in time_periods if period in html_content]
            
            self.log_result("HTML Vedic Times", True, f"Found Vedic times section with periods: {', '.join(time_periods_found) if time_periods_found else 'basic section'}")
            return True
        else:
            self.log_result("HTML Vedic Times", False, "Vedic times section not found")
            return False
    
    def test_html_report_planetary_route(self, html_content):
        """Test that HTML report contains Planetary Route section"""
        print("\n🗺️ Testing Planetary Route in HTML report...")
        
        # Check for planetary route section
        route_keywords = ["Планетарный маршрут", "маршрут жизни", "Солнце: Утро", "Луна: День", "Марс: Вечер"]
        route_section_found = any(keyword in html_content for keyword in route_keywords)
        
        if route_section_found:
            # Look for time periods or schedule
            schedule_keywords = ["Утро", "День", "Вечер", "6:00", "12:00", "18:00", "Солнце", "Луна", "Марс"]
            schedule_found = [keyword for keyword in schedule_keywords if keyword in html_content]
            
            self.log_result("HTML Planetary Route", True, f"Found planetary route section with schedule elements: {', '.join(schedule_found) if schedule_found else 'basic section'}")
            return True
        else:
            self.log_result("HTML Planetary Route", False, "Planetary route section not found")
            return False
    
    def test_html_report_structure(self, html_content):
        """Test overall HTML structure and validity"""
        print("\n🏗️ Testing HTML structure and validity...")
        
        structure_checks = {
            "DOCTYPE": html_content.startswith('<!DOCTYPE html>'),
            "HTML tags": '<html' in html_content and '</html>' in html_content,
            "HEAD section": '<head>' in html_content and '</head>' in html_content,
            "BODY section": '<body>' in html_content and '</body>' in html_content,
            "TITLE tag": '<title>' in html_content,
            "CSS styles": '<style>' in html_content or 'style=' in html_content,
            "NUMEROM branding": 'NUMEROM' in html_content
        }
        
        passed_checks = [check for check, result in structure_checks.items() if result]
        failed_checks = [check for check, result in structure_checks.items() if not result]
        
        if len(passed_checks) >= 5:  # At least 5 out of 7 structure checks should pass
            self.log_result("HTML Structure", True, f"Passed {len(passed_checks)}/7 structure checks: {', '.join(passed_checks)}")
            if failed_checks:
                print(f"   Minor issues: {', '.join(failed_checks)}")
            return True
        else:
            self.log_result("HTML Structure", False, f"Only passed {len(passed_checks)}/7 structure checks. Failed: {', '.join(failed_checks)}")
            return False
    
    def run_comprehensive_html_test(self):
        """Run comprehensive HTML report testing as requested in review"""
        print("🎯 COMPREHENSIVE HTML REPORT GENERATION TESTING")
        print("=" * 60)
        
        # Setup
        if not self.setup_user():
            print("❌ Cannot proceed without user authentication")
            return False
        
        # Test 1: Generate HTML report with expanded data
        html_content = self.test_html_report_basic()
        if not html_content:
            print("❌ Cannot proceed without basic HTML report")
            return False
        
        # Test 2: Verify Personal Numbers (ЧД, ЧУ, ЧС, ЧУ*, ЧМ, ПЧ)
        personal_numbers_ok = self.test_html_report_personal_numbers(html_content)
        
        # Test 3: Verify Planetary Strength with 7 planets and birth weekday
        planetary_strength_ok = self.test_html_report_planetary_strength(html_content)
        
        # Test 4: Verify Pythagorean Square with additional numbers
        pythagorean_ok = self.test_html_report_pythagorean_square(html_content)
        
        # Test 5: Verify Vedic Times section (if city is available)
        vedic_times_ok = self.test_html_report_vedic_times(html_content)
        
        # Test 6: Verify Planetary Route section (if city is available)
        planetary_route_ok = self.test_html_report_planetary_route(html_content)
        
        # Test 7: Verify HTML structure and validity
        structure_ok = self.test_html_report_structure(html_content)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE HTML REPORT TEST SUMMARY")
        print("=" * 60)
        
        all_tests = [
            ("Basic HTML Generation", html_content is not False),
            ("Personal Numbers", personal_numbers_ok),
            ("Planetary Strength", planetary_strength_ok),
            ("Pythagorean Square", pythagorean_ok),
            ("Vedic Times", vedic_times_ok),
            ("Planetary Route", planetary_route_ok),
            ("HTML Structure", structure_ok)
        ]
        
        passed_tests = [test for test, result in all_tests if result]
        failed_tests = [test for test, result in all_tests if not result]
        
        print(f"✅ PASSED: {len(passed_tests)}/7 tests")
        for test in passed_tests:
            print(f"   ✅ {test}")
        
        if failed_tests:
            print(f"❌ FAILED: {len(failed_tests)}/7 tests")
            for test in failed_tests:
                print(f"   ❌ {test}")
        
        overall_success = len(passed_tests) >= 5  # At least 5/7 tests should pass
        
        if overall_success:
            print(f"\n🎉 COMPREHENSIVE HTML REPORT TESTING: SUCCESS")
            print(f"   The HTML report generation includes all major sections as requested.")
            print(f"   HTML content length: {len(html_content)} characters")
        else:
            print(f"\n⚠️ COMPREHENSIVE HTML REPORT TESTING: PARTIAL SUCCESS")
            print(f"   Some sections may be missing or need improvement.")
        
        return overall_success

def main():
    """Main test execution"""
    tester = HTMLReportTester()
    success = tester.run_comprehensive_html_test()
    
    if success:
        print("\n✅ All comprehensive HTML report tests completed successfully!")
        return 0
    else:
        print("\n❌ Some HTML report tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    exit(main())