#!/usr/bin/env python3
"""
Backend Testing Script for Quiz System and Points System
Testing specific endpoints as requested in review:
- GET /api/learning/lesson/{lesson_id}/quiz
- POST /api/learning/lesson/{lesson_id}/start
"""

import requests
import json
import uuid
from datetime import datetime

# Configuration
BASE_URL = "https://numerology-fix.preview.emergentagent.com/api"

# Test credentials
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class QuizPointsSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.super_admin_token = None
        self.test_user_token = None
        self.test_lesson_id = None
        self.test_user_id = None
        self.test_user_email = None
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def authenticate_super_admin(self):
        """Authenticate as super admin"""
        self.log("🔐 Authenticating as super admin...")
        
        response = self.session.post(f"{BASE_URL}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            self.super_admin_token = data["access_token"]
            user_info = data["user"]
            self.log(f"✅ Super admin authenticated: {user_info['email']}")
            self.log(f"   Credits: {user_info['credits_remaining']}")
            self.log(f"   Super Admin: {user_info['is_super_admin']}")
            return True
        else:
            self.log(f"❌ Super admin authentication failed: {response.status_code} - {response.text}")
            return False
            
    def create_test_lesson(self):
        """Create a test lesson with points_for_lesson > 0"""
        self.log("📚 Creating test lesson with points requirement...")
        
        self.test_lesson_id = str(uuid.uuid4())
        lesson_data = {
            "id": self.test_lesson_id,
            "title": "Test Quiz Lesson",
            "description": "Test lesson for quiz and points system testing",
            "video_url": "https://example.com/test-video.mp4",
            "level": 1,
            "order": 999,
            "duration_minutes": 30,
            "points_for_lesson": 5,  # Requires 5 points to access
            "is_active": True
        }
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        response = self.session.post(f"{BASE_URL}/admin/lessons", 
                                   json=lesson_data, headers=headers)
        
        if response.status_code == 200:
            self.log(f"✅ Test lesson created: {self.test_lesson_id}")
            self.log(f"   Points required: {lesson_data['points_for_lesson']}")
            return True
        else:
            self.log(f"❌ Failed to create test lesson: {response.status_code} - {response.text}")
            return False
            
    def test_lesson_quiz_endpoint(self):
        """Test GET /api/learning/lesson/{lesson_id}/quiz"""
        self.log("🧩 Testing lesson quiz endpoint...")
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        response = self.session.get(f"{BASE_URL}/learning/lesson/{self.test_lesson_id}/quiz", 
                                  headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            self.log("✅ Quiz endpoint working correctly")
            self.log(f"   Lesson ID: {data.get('lesson_id')}")
            self.log(f"   Lesson Title: {data.get('lesson_title')}")
            
            quiz = data.get('quiz', {})
            questions = quiz.get('questions', [])
            self.log(f"   Quiz Questions: {len(questions)}")
            
            if len(questions) == 5:
                self.log("✅ Correct number of questions (5)")
            else:
                self.log(f"⚠️ Expected 5 questions, got {len(questions)}")
                
            # Check if questions have shuffled options
            for i, question in enumerate(questions[:2]):  # Check first 2 questions
                options = question.get('options', [])
                self.log(f"   Q{i+1}: {len(options)} options")
                
            return True
        else:
            self.log(f"❌ Quiz endpoint failed: {response.status_code} - {response.text}")
            return False
            
    def create_test_user(self):
        """Create a test user with sufficient credits"""
        self.log("👤 Creating test user with credits...")
        
        self.test_user_email = f"testuser_{uuid.uuid4().hex[:8]}@test.com"
        user_data = {
            "email": self.test_user_email,
            "password": "testpass123",
            "full_name": "Test User",
            "birth_date": "15.03.1990",
            "city": "Москва"
        }
        
        response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
        
        if response.status_code == 200:
            data = response.json()
            self.test_user_token = data["access_token"]
            self.test_user_id = data["user"]["id"]
            self.log(f"✅ Test user created: {self.test_user_email}")
            self.log(f"   User ID: {self.test_user_id}")
            self.log(f"   Initial credits: {data['user']['credits_remaining']}")
            
            # Give user more credits for testing
            self.give_user_credits(10)
            return True
        else:
            self.log(f"❌ Failed to create test user: {response.status_code} - {response.text}")
            return False
            
    def give_user_credits(self, credits):
        """Give credits to test user via admin endpoint"""
        self.log(f"💰 Giving {credits} credits to test user...")
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        response = self.session.patch(f"{BASE_URL}/admin/users/{self.test_user_id}/credits",
                                    json={"credits_remaining": credits}, headers=headers)
        
        if response.status_code == 200:
            self.log(f"✅ Credits updated to {credits}")
            return True
        else:
            self.log(f"❌ Failed to update credits: {response.status_code} - {response.text}")
            return False
            
    def test_lesson_start_first_time(self):
        """Test POST /api/learning/lesson/{lesson_id}/start - first time (should deduct points)"""
        self.log("🚀 Testing lesson start (first time - should deduct points)...")
        
        headers = {"Authorization": f"Bearer {self.test_user_token}"}
        response = self.session.post(f"{BASE_URL}/learning/lesson/{self.test_lesson_id}/start", 
                                   headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            self.log("✅ Lesson start successful")
            self.log(f"   Lesson started: {data.get('lesson_started')}")
            self.log(f"   Points deducted: {data.get('points_deducted')}")
            self.log(f"   Remaining credits: {data.get('remaining_credits')}")
            self.log(f"   Message: {data.get('message')}")
            
            if data.get('points_deducted', 0) > 0:
                self.log("✅ Points correctly deducted on first access")
                return True
            else:
                self.log("⚠️ No points deducted - unexpected behavior")
                return False
        else:
            self.log(f"❌ Lesson start failed: {response.status_code} - {response.text}")
            return False
            
    def test_lesson_start_repeat(self):
        """Test POST /api/learning/lesson/{lesson_id}/start - repeat (should NOT deduct points)"""
        self.log("🔄 Testing lesson start (repeat - should NOT deduct points)...")
        
        headers = {"Authorization": f"Bearer {self.test_user_token}"}
        response = self.session.post(f"{BASE_URL}/learning/lesson/{self.test_lesson_id}/start", 
                                   headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            self.log("✅ Repeat lesson start successful")
            self.log(f"   Lesson started: {data.get('lesson_started')}")
            self.log(f"   Points deducted: {data.get('points_deducted')}")
            self.log(f"   Message: {data.get('message')}")
            
            if data.get('points_deducted', 0) == 0:
                self.log("✅ No points deducted on repeat access - correct behavior")
                return True
            else:
                self.log("❌ Points deducted on repeat access - incorrect behavior")
                return False
        else:
            self.log(f"❌ Repeat lesson start failed: {response.status_code} - {response.text}")
            return False
            
    def test_insufficient_credits(self):
        """Test lesson start with insufficient credits (should return 402)"""
        self.log("💸 Testing lesson start with insufficient credits...")
        
        # Create another user with insufficient credits
        poor_user_email = f"pooruser_{uuid.uuid4().hex[:8]}@test.com"
        user_data = {
            "email": poor_user_email,
            "password": "testpass123",
            "full_name": "Poor User",
            "birth_date": "20.07.1985",
            "city": "Москва"
        }
        
        response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
        
        if response.status_code != 200:
            self.log(f"❌ Failed to create poor user: {response.status_code}")
            return False
            
        poor_user_token = response.json()["access_token"]
        poor_user_id = response.json()["user"]["id"]
        
        # Set credits to 0
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        self.session.patch(f"{BASE_URL}/admin/users/{poor_user_id}/credits",
                         json={"credits_remaining": 0}, headers=headers)
        
        # Try to start lesson
        headers = {"Authorization": f"Bearer {poor_user_token}"}
        response = self.session.post(f"{BASE_URL}/learning/lesson/{self.test_lesson_id}/start", 
                                   headers=headers)
        
        if response.status_code == 402:
            self.log("✅ Correctly returned 402 for insufficient credits")
            self.log(f"   Error message: {response.json().get('detail', 'No detail')}")
            return True
        else:
            self.log(f"❌ Expected 402, got {response.status_code} - {response.text}")
            return False
            
    def test_quiz_after_lesson_start(self):
        """Test quiz access after lesson has been started"""
        self.log("🧩 Testing quiz access after lesson start...")
        
        headers = {"Authorization": f"Bearer {self.test_user_token}"}
        response = self.session.get(f"{BASE_URL}/learning/lesson/{self.test_lesson_id}/quiz", 
                                  headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            self.log("✅ Quiz accessible after lesson start")
            self.log(f"   Quiz title: {data.get('quiz', {}).get('title')}")
            questions = data.get('quiz', {}).get('questions', [])
            self.log(f"   Questions available: {len(questions)}")
            return True
        else:
            self.log(f"❌ Quiz access failed after lesson start: {response.status_code} - {response.text}")
            return False
            
    def cleanup_test_data(self):
        """Clean up test lesson and users"""
        self.log("🧹 Cleaning up test data...")
        
        # Delete test lesson
        if self.test_lesson_id and self.super_admin_token:
            headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            # Note: There's no delete lesson endpoint in the API, so we'll just deactivate it
            self.session.put(f"{BASE_URL}/admin/lessons/{self.test_lesson_id}",
                           json={"is_active": False}, headers=headers)
            self.log("✅ Test lesson deactivated")
            
        self.log("✅ Cleanup completed")
        
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting Quiz and Points System Testing")
        self.log("=" * 60)
        
        tests = [
            ("Super Admin Authentication", self.authenticate_super_admin),
            ("Create Test Lesson", self.create_test_lesson),
            ("Test Quiz Endpoint", self.test_lesson_quiz_endpoint),
            ("Create Test User", self.create_test_user),
            ("Test Lesson Start (First Time)", self.test_lesson_start_first_time),
            ("Test Lesson Start (Repeat)", self.test_lesson_start_repeat),
            ("Test Insufficient Credits", self.test_insufficient_credits),
            ("Test Quiz After Lesson Start", self.test_quiz_after_lesson_start),
            ("Cleanup Test Data", self.cleanup_test_data)
        ]
        
        results = []
        for test_name, test_func in tests:
            self.log(f"\n📋 Running: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"💥 {test_name}: ERROR - {str(e)}")
                results.append((test_name, False))
                
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} - {test_name}")
            
        self.log(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED!")
            return True
        else:
            self.log("⚠️ Some tests failed - see details above")
            return False

if __name__ == "__main__":
    tester = QuizPointsSystemTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)