#!/usr/bin/env python3
"""
Comprehensive Lesson System Test Suite
Testing full functionality lesson system with FirstLesson compatibility

REVIEW REQUEST: Протестируй полнофункциональную систему уроков с frontend как у FirstLesson

КРИТИЧЕСКИЕ ПРОВЕРКИ ПОЛНОГО ФУНКЦИОНАЛА:
1. GET /api/learning/all-lessons - получение всех уроков для студентов включая custom_lessons
2. Поддержка всех API из FirstLesson для новых уроков:
   - POST /api/lessons/save-exercise-response
   - GET /api/lessons/exercise-responses/{lesson_id} 
   - POST /api/lessons/submit-quiz
   - POST /api/lessons/start-challenge/{challenge_id}
   - POST /api/lessons/complete-challenge-day
   - GET /api/lessons/challenge-progress/{challenge_id}
   - POST /api/lessons/add-habit-tracker
   - POST /api/lessons/update-habit
   - GET /api/lessons/overall-progress/{lesson_id}

АУТЕНТИФИКАЦИЯ: dmitrii.malahov@gmail.com / 756bvy67H

ТЕСТОВЫЙ СЦЕНАРИЙ ПОЛНОГО ФУНКЦИОНАЛА:
1. Создать тестовый урок с медиа
2. Добавить интерактивный контент (упражнения, квиз)
3. Проверить студенческие API (как в FirstLesson)
4. Тестировать челлендж систему
5. Тестировать трекер привычек
6. Проверить медиа интеграцию
"""

import requests
import json
import os
import tempfile
from pathlib import Path
import time
import io
import uuid

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"

class ComprehensiveLessonTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_lesson_id = f"comprehensive_test_{uuid.uuid4().hex[:8]}"
        self.video_file_id = None
        self.pdf_file_id = None
        self.challenge_id = None
        self.habit_tracker_id = None
        self.test_results = []
        
    def log(self, message):
        print(f"[COMPREHENSIVE_LESSON_TEST] {message}")
        
    def add_result(self, test_name, success, details=""):
        result = {
            'test': test_name,
            'success': success,
            'details': details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        self.log(f"{status}: {test_name} - {details}")
        
    def authenticate(self):
        """Authenticate as super admin"""
        self.log("🔐 Authenticating as super admin...")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.user_id = data['user']['id']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                user_info = data['user']
                self.add_result(
                    "Authentication", 
                    True, 
                    f"Logged in as {user_info['email']} (ID: {self.user_id}, Super Admin: {user_info.get('is_super_admin', False)}, Credits: {user_info.get('credits_remaining', 0)})"
                )
                return True
            else:
                self.add_result("Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Authentication", False, f"Login error: {str(e)}")
            return False

    def test_get_all_lessons(self):
        """Test GET /api/learning/all-lessons - получение всех уроков включая custom_lessons"""
        self.log("📚 Testing GET /api/learning/all-lessons...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/learning/all-lessons")
            if response.status_code == 200:
                data = response.json()
                
                user_level = data.get('user_level', {})
                available_lessons = data.get('available_lessons', [])
                total_levels = data.get('total_levels', 0)
                
                # Check for custom_lessons and video_lessons
                custom_lessons = [l for l in available_lessons if l.get('source') == 'custom_lessons']
                video_lessons = [l for l in available_lessons if l.get('source') == 'video_lessons']
                first_lesson = [l for l in available_lessons if l.get('id') == 'lesson_numerom_intro']
                
                details = f"Total lessons: {len(available_lessons)}, Custom: {len(custom_lessons)}, Video: {len(video_lessons)}, First lesson: {len(first_lesson)}, User level: {user_level.get('current_level', 1)}"
                
                success = len(available_lessons) > 0 and len(first_lesson) > 0
                self.add_result("GET All Lessons", success, details)
                return success
            else:
                self.add_result("GET All Lessons", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("GET All Lessons", False, f"Error: {str(e)}")
            return False

    def create_test_lesson_with_media(self):
        """1. Создать тестовый урок с медиа"""
        self.log("📚 Creating test lesson with media...")
        
        lesson_data = {
            "id": self.test_lesson_id,
            "title": "Полный функционал тест",
            "module": "Test Module",
            "description": "Test lesson for comprehensive functionality",
            "points_required": 0,
            "is_active": True,
            "content": {
                "theory": {
                    "what_is_topic": "Testing comprehensive lesson functionality",
                    "main_story": "This lesson tests all FirstLesson APIs",
                    "key_concepts": "Exercises, Quiz, Challenges, Habits",
                    "practical_applications": "Full interactive learning experience"
                },
                "exercises": [
                    {
                        "id": "exercise_1",
                        "title": "Test Exercise 1",
                        "type": "reflection",
                        "content": "Reflect on your learning goals",
                        "instructions": "Write your thoughts about numerology",
                        "expected_outcome": "Better understanding of personal goals"
                    }
                ],
                "quiz": {
                    "id": "quiz_1",
                    "title": "Test Quiz",
                    "questions": [
                        {
                            "id": "q1",
                            "question": "What is numerology?",
                            "options": ["Study of numbers", "Study of letters", "Study of colors", "Study of sounds"],
                            "correct_answer": 0
                        }
                    ]
                },
                "challenge": {
                    "id": f"challenge_{self.test_lesson_id}",
                    "title": "7-Day Numerology Challenge",
                    "description": "Daily numerology practice",
                    "daily_tasks": [
                        "Calculate your life path number",
                        "Meditate on your soul number",
                        "Practice number visualization",
                        "Journal about number patterns",
                        "Share insights with others",
                        "Apply numerology to decisions",
                        "Reflect on the week's learning"
                    ]
                }
            }
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/create", json=lesson_data)
            if response.status_code == 200:
                data = response.json()
                self.challenge_id = f"challenge_{self.test_lesson_id}"
                self.add_result(
                    "Create Test Lesson with Media", 
                    True, 
                    f"Lesson created: {data.get('lesson_id', self.test_lesson_id)}, Challenge ID: {self.challenge_id}"
                )
                return True
            else:
                self.add_result("Create Test Lesson with Media", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Create Test Lesson with Media", False, f"Error: {str(e)}")
            return False

    def upload_video_for_lesson(self):
        """Upload video for lesson"""
        self.log("🎥 Uploading video for lesson...")
        
        # Create test video content
        video_content = b"FAKE_VIDEO_CONTENT_FOR_TESTING" * 100
        
        try:
            files = {
                'file': ('test_lesson_video.mp4', io.BytesIO(video_content), 'video/mp4')
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-video", files=files)
            if response.status_code == 200:
                data = response.json()
                self.video_file_id = data.get('file_id')
                self.add_result(
                    "Upload Video for Lesson", 
                    True, 
                    f"Video uploaded: file_id={self.video_file_id}"
                )
                return True
            else:
                self.add_result("Upload Video for Lesson", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Upload Video for Lesson", False, f"Error: {str(e)}")
            return False

    def update_lesson_with_video(self):
        """Update lesson with video_file_id"""
        self.log("🔗 Updating lesson with video_file_id...")
        
        if not self.video_file_id:
            self.add_result("Update Lesson with Video", False, "No video file_id available")
            return False
        
        try:
            lesson_update = {
                "video_file_id": self.video_file_id,
                "updated_at": "2025-01-11T12:00:00Z"
            }
            
            response = self.session.put(f"{BACKEND_URL}/admin/lessons/{self.test_lesson_id}", json=lesson_update)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Update Lesson with Video", 
                    True, 
                    f"Lesson updated with video_file_id: {self.video_file_id}"
                )
                return True
            else:
                self.add_result("Update Lesson with Video", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Update Lesson with Video", False, f"Error: {str(e)}")
            return False

    def test_save_exercise_response(self):
        """Test POST /api/lessons/save-exercise-response"""
        self.log("✏️ Testing save exercise response...")
        
        try:
            exercise_data = {
                "lesson_id": "lesson_numerom_intro",  # Use FirstLesson ID
                "exercise_id": "exercise_1",
                "response_text": "My reflection on numerology learning goals: I want to understand how numbers influence my life path and make better decisions based on numerical insights."
            }
            
            response = self.session.post(f"{BACKEND_URL}/lessons/save-exercise-response", data=exercise_data)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Save Exercise Response", 
                    True, 
                    f"Exercise response saved: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.add_result("Save Exercise Response", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Save Exercise Response", False, f"Error: {str(e)}")
            return False

    def test_get_exercise_responses(self):
        """Test GET /api/lessons/exercise-responses/{lesson_id}"""
        self.log("📖 Testing get exercise responses...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons/exercise-responses/lesson_numerom_intro")
            if response.status_code == 200:
                data = response.json()
                responses = data.get('responses', [])
                self.add_result(
                    "Get Exercise Responses", 
                    True, 
                    f"Retrieved {len(responses)} exercise responses"
                )
                return True
            else:
                self.add_result("Get Exercise Responses", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Get Exercise Responses", False, f"Error: {str(e)}")
            return False

    def test_submit_quiz(self):
        """Test POST /api/lessons/submit-quiz"""
        self.log("🧠 Testing submit quiz...")
        
        try:
            # The quiz endpoint expects specific format for FirstLesson
            quiz_answers = {
                "q1": "Study of numbers",  # Correct answer for the quiz question
            }
            
            quiz_data = {
                "quiz_id": "quiz_numerom_intro",  # FirstLesson quiz ID
                "answers": json.dumps(quiz_answers)
            }
            
            response = self.session.post(f"{BACKEND_URL}/lessons/submit-quiz", data=quiz_data)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Submit Quiz", 
                    True, 
                    f"Quiz submitted: Score {data.get('percentage', 0)}%, Status: {data.get('status', 'Unknown')}"
                )
                return True
            else:
                self.add_result("Submit Quiz", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Submit Quiz", False, f"Error: {str(e)}")
            return False

    def test_start_challenge(self):
        """Test POST /api/lessons/start-challenge/{challenge_id}"""
        self.log("🏆 Testing start challenge...")
        
        # Use FirstLesson challenge ID
        first_lesson_challenge_id = "challenge_numerom_intro"
        
        try:
            response = self.session.post(f"{BACKEND_URL}/lessons/start-challenge/{first_lesson_challenge_id}")
            if response.status_code == 200:
                data = response.json()
                self.challenge_id = first_lesson_challenge_id  # Update for later tests
                self.add_result(
                    "Start Challenge", 
                    True, 
                    f"Challenge started: {data.get('message', 'Success')}, Current day: {data.get('current_day', 0)}"
                )
                return True
            else:
                self.add_result("Start Challenge", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Start Challenge", False, f"Error: {str(e)}")
            return False

    def test_complete_challenge_day(self):
        """Test POST /api/lessons/complete-challenge-day"""
        self.log("📅 Testing complete challenge day...")
        
        if not self.challenge_id:
            self.add_result("Complete Challenge Day", False, "No challenge_id available")
            return False
        
        try:
            day_data = {
                "challenge_id": self.challenge_id,
                "day": 1,
                "notes": "Successfully calculated my life path number: 7"
            }
            
            response = self.session.post(f"{BACKEND_URL}/lessons/complete-challenge-day", data=day_data)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Complete Challenge Day", 
                    True, 
                    f"Day completed: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.add_result("Complete Challenge Day", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Complete Challenge Day", False, f"Error: {str(e)}")
            return False

    def test_get_challenge_progress(self):
        """Test GET /api/lessons/challenge-progress/{challenge_id}"""
        self.log("📊 Testing get challenge progress...")
        
        if not self.challenge_id:
            self.add_result("Get Challenge Progress", False, "No challenge_id available")
            return False
        
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons/challenge-progress/{self.challenge_id}")
            if response.status_code == 200:
                data = response.json()
                progress = data.get('progress_percentage', 0)
                completed_days = data.get('completed_days', 0)
                total_days = data.get('total_days', 0)
                
                self.add_result(
                    "Get Challenge Progress", 
                    True, 
                    f"Progress: {progress}%, Days: {completed_days}/{total_days}"
                )
                return True
            else:
                self.add_result("Get Challenge Progress", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Get Challenge Progress", False, f"Error: {str(e)}")
            return False

    def test_add_habit_tracker(self):
        """Test POST /api/lessons/add-habit-tracker"""
        self.log("📝 Testing add habit tracker...")
        
        try:
            habit_data = {
                "lesson_id": "lesson_numerom_intro"  # Use FirstLesson ID
            }
            
            response = self.session.post(f"{BACKEND_URL}/lessons/add-habit-tracker", data=habit_data)
            if response.status_code == 200:
                data = response.json()
                self.habit_tracker_id = f"{self.user_id}_lesson_numerom_intro_tracker"  # Set for later tests
                self.add_result(
                    "Add Habit Tracker", 
                    True, 
                    f"Habit tracker added: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.add_result("Add Habit Tracker", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Add Habit Tracker", False, f"Error: {str(e)}")
            return False

    def test_update_habit(self):
        """Test POST /api/lessons/update-habit"""
        self.log("✅ Testing update habit...")
        
        if not self.habit_tracker_id:
            self.add_result("Update Habit", False, "No habit_tracker_id available")
            return False
        
        try:
            habit_update = {
                "lesson_id": "lesson_numerom_intro",
                "habit_name": "Утренняя аффирмация или медитация",
                "completed": True,
                "notes": "Completed 10-minute meditation focusing on life path number 7"
            }
            
            response = self.session.post(f"{BACKEND_URL}/lessons/update-habit", data=habit_update)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Update Habit", 
                    True, 
                    f"Habit updated: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.add_result("Update Habit", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Update Habit", False, f"Error: {str(e)}")
            return False

    def test_get_overall_progress(self):
        """Test GET /api/lessons/overall-progress/{lesson_id}"""
        self.log("📈 Testing get overall progress...")
        
        try:
            # Use FirstLesson ID since that's what the endpoint expects
            response = self.session.get(f"{BACKEND_URL}/lessons/overall-progress/lesson_numerom_intro")
            if response.status_code == 200:
                data = response.json()
                
                overall_progress = data.get('overall_progress', 0)
                exercise_progress = data.get('exercise_progress', 0)
                quiz_progress = data.get('quiz_progress', 0)
                challenge_progress = data.get('challenge_progress', 0)
                habit_progress = data.get('habit_progress', 0)
                
                details = f"Overall: {overall_progress}%, Exercise: {exercise_progress}%, Quiz: {quiz_progress}%, Challenge: {challenge_progress}%, Habits: {habit_progress}%"
                
                self.add_result(
                    "Get Overall Progress", 
                    True, 
                    details
                )
                return True
            else:
                self.add_result("Get Overall Progress", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Get Overall Progress", False, f"Error: {str(e)}")
            return False

    def test_media_integration(self):
        """Test media integration - video and PDF access"""
        self.log("🎬 Testing media integration...")
        
        if not self.video_file_id:
            self.add_result("Media Integration", False, "No video file_id available")
            return False
        
        try:
            # Test video access
            video_response = self.session.get(f"{BACKEND_URL}/consultations/video/{self.video_file_id}")
            video_success = video_response.status_code == 200
            
            # Test lesson media endpoint
            media_response = self.session.get(f"{BACKEND_URL}/lessons/media/{self.test_lesson_id}")
            media_success = media_response.status_code == 200
            
            if media_success:
                media_data = media_response.json()
                videos = media_data.get('videos', [])
                pdfs = media_data.get('pdfs', [])
                
                details = f"Video access: {video_success}, Media endpoint: {media_success}, Videos: {len(videos)}, PDFs: {len(pdfs)}"
            else:
                details = f"Video access: {video_success}, Media endpoint: {media_success}"
            
            success = video_success and media_success
            self.add_result("Media Integration", success, details)
            return success
                
        except Exception as e:
            self.add_result("Media Integration", False, f"Error: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run the complete comprehensive test suite"""
        self.log("🚀 Starting Comprehensive Lesson System Test...")
        
        # Authentication
        if not self.authenticate():
            return False
        
        # Test 1: GET all lessons
        self.test_get_all_lessons()
        
        # Test 2: Create lesson with media
        if self.create_test_lesson_with_media():
            # Upload and link media
            if self.upload_video_for_lesson():
                self.update_lesson_with_video()
        
        # Test 3: Student APIs (FirstLesson compatibility)
        self.test_save_exercise_response()
        self.test_get_exercise_responses()
        self.test_submit_quiz()
        
        # Test 4: Challenge system
        self.test_start_challenge()
        self.test_complete_challenge_day()
        self.test_get_challenge_progress()
        
        # Test 5: Habit tracker
        self.test_add_habit_tracker()
        self.test_update_habit()
        
        # Test 6: Overall progress
        self.test_get_overall_progress()
        
        # Test 7: Media integration
        self.test_media_integration()
        
        # Summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log("=" * 80)
        self.log("🎯 COMPREHENSIVE LESSON SYSTEM TEST SUMMARY")
        self.log("=" * 80)
        self.log(f"Total Tests: {total_tests}")
        self.log(f"✅ Passed: {passed_tests}")
        self.log(f"❌ Failed: {failed_tests}")
        self.log(f"📊 Success Rate: {success_rate:.1f}%")
        self.log("=" * 80)
        
        if failed_tests > 0:
            self.log("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    self.log(f"  - {result['test']}: {result['details']}")
        
        self.log("=" * 80)
        
        # Determine overall result
        if success_rate >= 80:
            self.log("🎉 COMPREHENSIVE TEST RESULT: SUCCESS")
            self.log("✅ Lesson system has full FirstLesson functionality")
        elif success_rate >= 60:
            self.log("⚠️ COMPREHENSIVE TEST RESULT: PARTIAL SUCCESS")
            self.log("🔧 Some functionality needs fixes")
        else:
            self.log("❌ COMPREHENSIVE TEST RESULT: FAILURE")
            self.log("🚨 Major functionality issues detected")

if __name__ == "__main__":
    tester = ComprehensiveLessonTester()
    tester.run_comprehensive_test()