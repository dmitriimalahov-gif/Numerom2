#!/usr/bin/env python3
"""
NUMEROM Review Request Testing Suite - Local Version
Testing all new NUMEROM features locally as specified in the review request
"""

import requests
import json
from datetime import datetime
import time

# Use local backend URL
BACKEND_URL = "http://localhost:8001/api"

class LocalReviewRequestTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.super_admin_token = None
        self.regular_user_token = None
        self.regular_user_id = None
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
        token = self.super_admin_token if use_super_admin else self.regular_user_token
        if token and "Authorization" not in default_headers:
            default_headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=10)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data, headers=default_headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {method} {url}: {str(e)}")
            return None
    
    def test_super_admin_login(self):
        """Test super admin login with provided credentials"""
        response = self.make_request("POST", "/auth/login", self.super_admin_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.super_admin_token = data["access_token"]
                user_info = data["user"]
                
                # Verify super admin status and credits
                if user_info.get("is_super_admin") and user_info.get("credits_remaining") == 1000000:
                    self.log_result("Super Admin Login", True, 
                                  f"Super admin logged in successfully with {user_info.get('credits_remaining')} credits")
                    return True
                else:
                    self.log_result("Super Admin Login", False, 
                                  f"User not super admin or wrong credits: {user_info}")
            else:
                self.log_result("Super Admin Login", False, "Missing token or user data", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Super Admin Login", False, "Super admin login failed", error)
        return False
    
    def test_create_regular_user(self):
        """Create a regular user for testing admin functions"""
        timestamp = int(time.time())
        regular_user_data = {
            "email": f"testuser{timestamp}@numerom.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "birth_date": "10.01.1982",
            "city": "Москва"
        }
        
        response = self.make_request("POST", "/auth/register", regular_user_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.regular_user_token = data["access_token"]
                self.regular_user_id = data["user"]["id"]
                self.log_result("Create Regular User", True, 
                              f"Regular user created with ID: {self.regular_user_id}")
                return True
            else:
                self.log_result("Create Regular User", False, "Missing token or user data", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Create Regular User", False, "Failed to create regular user", error)
        return False
    
    # ===== ADMIN PANEL TESTS =====
    
    def test_admin_get_all_users(self):
        """Test GET /api/admin/users - get all users with progress"""
        if not self.super_admin_token:
            self.log_result("Admin Get All Users", False, "No super admin token available")
            return False
        
        response = self.make_request("GET", "/admin/users", use_super_admin=True)
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Check response structure
            if "users" in data and "total_count" in data:
                users = data["users"]
                if isinstance(users, list) and len(users) > 0:
                    # Check first user structure
                    first_user = users[0]
                    required_fields = ["id", "email", "name", "birth_date", "city", 
                                     "credits_remaining", "is_premium", "subscription_type",
                                     "lessons_completed", "lessons_total", "lessons_progress_percent"]
                    
                    if all(field in first_user for field in required_fields):
                        # Look for our super admin user
                        super_admin_user = next((u for u in users if u["email"] == "dmitrii.malahov@gmail.com"), None)
                        if super_admin_user and super_admin_user["credits_remaining"] == 1000000:
                            self.log_result("Admin Get All Users", True, 
                                          f"Retrieved {len(users)} users with progress data, super admin found")
                            return True
                        else:
                            self.log_result("Admin Get All Users", False, 
                                          "Super admin not found or wrong credits", super_admin_user)
                    else:
                        missing = [f for f in required_fields if f not in first_user]
                        self.log_result("Admin Get All Users", False, 
                                      f"Missing user fields: {missing}", first_user)
                else:
                    self.log_result("Admin Get All Users", False, 
                                  f"No users found or invalid format: {type(users)}", data)
            else:
                self.log_result("Admin Get All Users", False, 
                              "Missing users or total_count in response", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Admin Get All Users", False, "Failed to get users", error)
        return False
    
    def test_admin_update_user_credits(self):
        """Test PATCH /api/admin/users/{user_id}/credits - change user credits"""
        if not self.super_admin_token or not self.regular_user_id:
            self.log_result("Admin Update User Credits", False, "Missing super admin token or regular user ID")
            return False
        
        # Test updating credits to 50
        new_credits = 50
        credits_data = {"credits_remaining": new_credits}
        
        response = self.make_request("PATCH", f"/admin/users/{self.regular_user_id}/credits", 
                                   credits_data, use_super_admin=True)
        
        if response and response.status_code == 200:
            data = response.json()
            
            if "success" in data and "new_credits" in data:
                if data["success"] and data["new_credits"] == new_credits:
                    self.log_result("Admin Update User Credits", True, 
                                  f"Successfully updated user credits to {new_credits}")
                    return True
                else:
                    self.log_result("Admin Update User Credits", False, 
                                  f"Update failed or wrong credits: {data}")
            else:
                self.log_result("Admin Update User Credits", False, 
                              "Missing success or new_credits in response", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Admin Update User Credits", False, "Failed to update user credits", error)
        return False
    
    def test_admin_get_user_lessons_progress(self):
        """Test GET /api/admin/users/{user_id}/lessons - detailed lesson progress"""
        if not self.super_admin_token or not self.regular_user_id:
            self.log_result("Admin Get User Lessons Progress", False, "Missing super admin token or regular user ID")
            return False
        
        response = self.make_request("GET", f"/admin/users/{self.regular_user_id}/lessons", 
                                   use_super_admin=True)
        
        if response and response.status_code == 200:
            data = response.json()
            
            if "lessons" in data and "user_id" in data:
                lessons = data["lessons"]
                if data["user_id"] == self.regular_user_id:
                    if isinstance(lessons, list):
                        # Empty lessons list is valid for new user
                        self.log_result("Admin Get User Lessons Progress", True, 
                                      f"Retrieved {len(lessons)} lesson progress records for user")
                        return True
                    else:
                        self.log_result("Admin Get User Lessons Progress", False, 
                                      f"Lessons not a list: {type(lessons)}", data)
                else:
                    self.log_result("Admin Get User Lessons Progress", False, 
                                  f"Wrong user_id in response: {data['user_id']}")
            else:
                self.log_result("Admin Get User Lessons Progress", False, 
                              "Missing lessons or user_id in response", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Admin Get User Lessons Progress", False, "Failed to get user lessons progress", error)
        return False
    
    # ===== PLANETARY ROUTES TESTS =====
    
    def test_planetary_route_basic(self):
        """Test GET /api/vedic-time/planetary-route - basic daily route"""
        if not self.regular_user_token:
            self.log_result("Planetary Route Basic", False, "No regular user token available")
            return False
        
        # Test with Moscow
        params = {"city": "Москва", "date": "2025-01-15"}
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/vedic-time/planetary-route?{query_string}"
        
        response = self.make_request("GET", endpoint)
        
        if response and response.status_code == 200:
            data = response.json()
            required_fields = ["date", "city", "personal_birth_date", "daily_ruling_planet", 
                             "best_activity_hours", "avoid_periods", "favorable_period", 
                             "hourly_guide", "daily_recommendations"]
            
            if all(field in data for field in required_fields):
                # Check avoid periods structure
                avoid_periods = data.get("avoid_periods", {})
                if "rahu_kaal" in avoid_periods and "gulika_kaal" in avoid_periods and "yamaghanta" in avoid_periods:
                    # Check favorable period
                    favorable_period = data.get("favorable_period", {})
                    if favorable_period:  # Should have Abhijit Muhurta
                        best_hours = data.get("best_activity_hours", [])
                        if isinstance(best_hours, list):
                            self.log_result("Planetary Route Basic", True, 
                                          f"Route retrieved with {len(best_hours)} best hours and all periods")
                            return True
                        else:
                            self.log_result("Planetary Route Basic", False, 
                                          "Best activity hours not a list", data)
                    else:
                        self.log_result("Planetary Route Basic", False, 
                                      "Missing favorable period", data)
                else:
                    self.log_result("Planetary Route Basic", False, 
                                  "Missing avoid periods", avoid_periods)
            else:
                missing = [f for f in required_fields if f not in data]
                self.log_result("Planetary Route Basic", False, 
                              f"Missing fields: {missing}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Planetary Route Basic", False, 
                          "Failed to get planetary route", error)
        return False
    
    def test_planetary_route_monthly(self):
        """Test GET /api/vedic-time/planetary-route/monthly - monthly plan"""
        if not self.regular_user_token:
            self.log_result("Planetary Route Monthly", False, "No regular user token available")
            return False
        
        # Test with Moscow
        params = {"city": "Москва", "date": "2025-01-15"}
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/vedic-time/planetary-route/monthly?{query_string}"
        
        response = self.make_request("GET", endpoint)
        
        if response and response.status_code == 200:
            data = response.json()
            required_fields = ["period", "start_date", "end_date", "city", "total_days", "daily_schedule"]
            
            if all(field in data for field in required_fields):
                daily_schedule = data.get("daily_schedule", [])
                if isinstance(daily_schedule, list) and len(daily_schedule) == 30:  # Should be 30 days
                    self.log_result("Planetary Route Monthly", True, 
                                  f"Monthly plan retrieved with {len(daily_schedule)} days")
                    return True
                else:
                    self.log_result("Planetary Route Monthly", False, 
                                  f"Expected 30 days, got {len(daily_schedule) if isinstance(daily_schedule, list) else 'invalid'}", data)
            else:
                missing = [f for f in required_fields if f not in data]
                self.log_result("Planetary Route Monthly", False, 
                              f"Missing fields: {missing}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Planetary Route Monthly", False, 
                          "Failed to get monthly route", error)
        return False
    
    def test_planetary_route_quarterly(self):
        """Test GET /api/vedic-time/planetary-route/quarterly - quarterly plan"""
        if not self.regular_user_token:
            self.log_result("Planetary Route Quarterly", False, "No regular user token available")
            return False
        
        # Test with Moscow
        params = {"city": "Москва", "date": "2025-01-15"}
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/vedic-time/planetary-route/quarterly?{query_string}"
        
        response = self.make_request("GET", endpoint)
        
        if response and response.status_code == 200:
            data = response.json()
            required_fields = ["period", "start_date", "end_date", "city", "total_days"]
            
            if all(field in data for field in required_fields):
                total_days = data.get("total_days", 0)
                if total_days >= 90:  # Should be around 90 days for a quarter
                    self.log_result("Planetary Route Quarterly", True, 
                                  f"Quarterly plan retrieved with {total_days} days")
                    return True
                else:
                    self.log_result("Planetary Route Quarterly", False, 
                                  f"Expected ~90 days, got {total_days}", data)
            else:
                missing = [f for f in required_fields if f not in data]
                self.log_result("Planetary Route Quarterly", False, 
                              f"Missing fields: {missing}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Planetary Route Quarterly", False, 
                          "Failed to get quarterly route", error)
        return False
    
    # ===== VEDIC TIMES TESTS =====
    
    def test_vedic_daily_schedule(self):
        """Test GET /api/vedic-time/daily-schedule - full vedic periods"""
        if not self.regular_user_token:
            self.log_result("Vedic Daily Schedule", False, "No regular user token available")
            return False
        
        # Test with Moscow
        params = {"city": "Москва", "date": "2025-01-15"}
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/vedic-time/daily-schedule?{query_string}"
        
        response = self.make_request("GET", endpoint)
        
        if response and response.status_code == 200:
            data = response.json()
            required_fields = ["city", "date", "weekday", "sun_times", "inauspicious_periods", 
                             "auspicious_periods", "planetary_hours", "recommendations"]
            
            if all(field in data for field in required_fields):
                # Check inauspicious periods with Sanskrit terminology
                inauspicious = data.get("inauspicious_periods", {})
                required_inauspicious = ["rahu_kaal", "gulika_kaal", "yamaghanta"]
                
                if all(period in inauspicious for period in required_inauspicious):
                    # Check auspicious periods
                    auspicious = data.get("auspicious_periods", {})
                    if "abhijit_muhurta" in auspicious:
                        # Check planetary hours
                        planetary_hours = data.get("planetary_hours", [])
                        if isinstance(planetary_hours, list) and len(planetary_hours) > 0:
                            # Verify Sanskrit terminology in content
                            content_str = str(data)
                            if "राहु" in content_str or "Rahu" in content_str:
                                self.log_result("Vedic Daily Schedule", True, 
                                              f"Complete schedule with Sanskrit terminology and {len(planetary_hours)} planetary hours")
                                return True
                            else:
                                self.log_result("Vedic Daily Schedule", False, 
                                              "Missing Sanskrit terminology", data)
                        else:
                            self.log_result("Vedic Daily Schedule", False, 
                                          "Missing or empty planetary hours", data)
                    else:
                        self.log_result("Vedic Daily Schedule", False, 
                                      "Missing Abhijit Muhurta", auspicious)
                else:
                    missing = [p for p in required_inauspicious if p not in inauspicious]
                    self.log_result("Vedic Daily Schedule", False, 
                                  f"Missing inauspicious periods: {missing}", inauspicious)
            else:
                missing = [f for f in required_fields if f not in data]
                self.log_result("Vedic Daily Schedule", False, 
                              f"Missing fields: {missing}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Vedic Daily Schedule", False, 
                          "Failed to get vedic schedule", error)
        return False
    
    def run_all_tests(self):
        """Run all review request tests"""
        print("🚀 Starting NUMEROM Review Request Testing Suite (Local)")
        print("=" * 70)
        print("Testing all new NUMEROM features as specified in the review request")
        print("=" * 70)
        
        # Setup phase
        print("\n🔧 SETUP PHASE:")
        if not self.test_super_admin_login():
            print("❌ Cannot proceed without super admin access")
            return 0, 1
        
        if not self.test_create_regular_user():
            print("❌ Cannot proceed without regular user")
            return 0, 2
        
        # Admin Panel Tests
        print("\n👑 ADMIN PANEL TESTS:")
        self.test_admin_get_all_users()
        self.test_admin_update_user_credits()
        self.test_admin_get_user_lessons_progress()
        
        # Planetary Routes Tests
        print("\n🌟 PLANETARY ROUTES TESTS:")
        self.test_planetary_route_basic()
        self.test_planetary_route_monthly()
        self.test_planetary_route_quarterly()
        
        # Vedic Times Tests
        print("\n🕉️ VEDIC TIMES TESTS:")
        self.test_vedic_daily_schedule()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 REVIEW REQUEST TEST SUMMARY")
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
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        # Show category results
        categories = {
            "Admin Panel": ["Admin"],
            "Planetary Routes": ["Planetary Route"],
            "Vedic Times": ["Vedic Daily Schedule"]
        }
        
        print("\n📋 CATEGORY RESULTS:")
        for category, keywords in categories.items():
            category_tests = [r for r in self.test_results if any(kw in r['test'] for kw in keywords)]
            if category_tests:
                category_passed = sum(1 for t in category_tests if t["success"])
                category_total = len(category_tests)
                status = "✅" if category_passed == category_total else "❌"
                print(f"  {status} {category}: {category_passed}/{category_total}")
        
        return passed, total

def main():
    """Main test execution"""
    tester = LocalReviewRequestTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        print("\n🎉 All review request tests passed!")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        exit(1)

if __name__ == "__main__":
    main()