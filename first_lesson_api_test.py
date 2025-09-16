#!/usr/bin/env python3
"""
Comprehensive API Testing for FirstLesson Component - NumerOM
=============================================================

Тестирование всех API endpoints для компонента FirstLesson согласно review request:

ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. GET /api/lessons/first-lesson - получить данные первого урока 
2. POST /api/lessons/start-challenge/{challenge_id} - начать челлендж (challenge_sun_7days)
3. POST /api/lessons/complete-challenge-day - отметить день челленджа как выполненный  
4. GET /api/lessons/challenge-progress/{challenge_id} - получить прогресс челленджа
5. POST /api/lessons/submit-quiz - отправить ответы на квиз (quiz_intro_1)
6. POST /api/lessons/add-habit-tracker - добавить трекер привычек
7. POST /api/lessons/update-habit - обновить статус привычки
8. GET /api/lessons/user-progress/{lesson_id} - получить прогресс пользователя

ТЕСТОВЫЕ ДАННЫЕ:
- Пользователь: dmitrii.malahov@gmail.com / 756bvy67H
- lesson_id: "lesson_numerom_intro"  
- challenge_id: "challenge_sun_7days"
- quiz_id: "quiz_intro_1"
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"
LESSON_ID = "lesson_numerom_intro"
CHALLENGE_ID = "challenge_sun_7days"
QUIZ_ID = "quiz_intro_1"

class FirstLessonAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Логирование результатов тестов"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def authenticate(self):
        """Аутентификация тестового пользователя"""
        print("🔐 STEP 1: Authenticating test user...")
        
        try:
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log_test(
                    "User Authentication", 
                    True, 
                    f"Successfully authenticated as {user_info.get('email', 'unknown')} with {user_info.get('credits_remaining', 0)} credits"
                )
                return True
            else:
                self.log_test(
                    "User Authentication", 
                    False, 
                    f"Login failed with status {response.status_code}",
                    response.json() if response.content else {}
                )
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_get_first_lesson(self):
        """Тест 1: GET /api/lessons/first-lesson"""
        print("📚 STEP 2: Testing GET /api/lessons/first-lesson...")
        
        try:
            response = self.session.get(f"{BASE_URL}/lessons/first-lesson")
            
            if response.status_code == 200:
                data = response.json()
                lesson = data.get("lesson", {})
                
                # Проверяем структуру урока
                required_fields = ["id", "title", "module", "content", "exercises", "quiz", "challenges", "habit_tracker"]
                missing_fields = [field for field in required_fields if field not in lesson]
                
                if not missing_fields:
                    # Проверяем конкретные данные
                    lesson_id_correct = lesson.get("id") == LESSON_ID
                    has_quiz = lesson.get("quiz") and lesson["quiz"].get("id") == QUIZ_ID
                    has_challenge = any(ch.get("id") == CHALLENGE_ID for ch in lesson.get("challenges", []))
                    has_exercises = len(lesson.get("exercises", [])) > 0
                    
                    if lesson_id_correct and has_quiz and has_challenge and has_exercises:
                        self.log_test(
                            "Get First Lesson Data", 
                            True, 
                            f"Lesson loaded: {lesson.get('title', 'Unknown')} with {len(lesson.get('exercises', []))} exercises, quiz '{lesson.get('quiz', {}).get('id', 'None')}', and {len(lesson.get('challenges', []))} challenges"
                        )
                        return True
                    else:
                        self.log_test(
                            "Get First Lesson Data", 
                            False, 
                            f"Lesson data incomplete: lesson_id={lesson_id_correct}, has_quiz={has_quiz}, has_challenge={has_challenge}, has_exercises={has_exercises}"
                        )
                        return False
                else:
                    self.log_test(
                        "Get First Lesson Data", 
                        False, 
                        f"Missing required fields: {missing_fields}"
                    )
                    return False
            else:
                self.log_test(
                    "Get First Lesson Data", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.json() if response.content else {}
                )
                return False
                
        except Exception as e:
            self.log_test("Get First Lesson Data", False, f"Error: {str(e)}")
            return False

    def test_start_challenge(self):
        """Тест 2: POST /api/lessons/start-challenge/{challenge_id}"""
        print("🏃 STEP 3: Testing POST /api/lessons/start-challenge/challenge_sun_7days...")
        
        try:
            response = self.session.post(f"{BASE_URL}/lessons/start-challenge/{CHALLENGE_ID}")
            
            if response.status_code == 200:
                data = response.json()
                challenge = data.get("challenge", {})
                
                # Проверяем данные челленджа
                challenge_id_correct = challenge.get("id") == CHALLENGE_ID
                has_daily_tasks = len(challenge.get("daily_tasks", [])) == 7
                has_start_date = "start_date" in data
                current_day_correct = data.get("current_day") == 1
                
                if challenge_id_correct and has_daily_tasks and has_start_date and current_day_correct:
                    self.log_test(
                        "Start Challenge", 
                        True, 
                        f"Challenge '{challenge.get('title', 'Unknown')}' started successfully with {len(challenge.get('daily_tasks', []))} daily tasks"
                    )
                    return True
                else:
                    self.log_test(
                        "Start Challenge", 
                        False, 
                        f"Challenge data incomplete: id={challenge_id_correct}, tasks={has_daily_tasks}, start_date={has_start_date}, current_day={current_day_correct}"
                    )
                    return False
            else:
                self.log_test(
                    "Start Challenge", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.json() if response.content else {}
                )
                return False
                
        except Exception as e:
            self.log_test("Start Challenge", False, f"Error: {str(e)}")
            return False

    def test_complete_challenge_day(self):
        """Тест 3: POST /api/lessons/complete-challenge-day"""
        print("✅ STEP 4: Testing POST /api/lessons/complete-challenge-day...")
        
        try:
            # Отмечаем день 1 как выполненный
            form_data = {
                "challenge_id": CHALLENGE_ID,
                "day": 1,
                "notes": "Completed first day of sun energy challenge - wrote down my strengths and practiced affirmations"
            }
            
            response = self.session.post(f"{BASE_URL}/lessons/complete-challenge-day", data=form_data)
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                
                if "День 1" in message and "выполненный" in message:
                    self.log_test(
                        "Complete Challenge Day", 
                        True, 
                        f"Day 1 marked as completed: {message}"
                    )
                    return True
                else:
                    self.log_test(
                        "Complete Challenge Day", 
                        False, 
                        f"Unexpected response message: {message}"
                    )
                    return False
            else:
                self.log_test(
                    "Complete Challenge Day", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.json() if response.content else {}
                )
                return False
                
        except Exception as e:
            self.log_test("Complete Challenge Day", False, f"Error: {str(e)}")
            return False

    def test_get_challenge_progress(self):
        """Тест 4: GET /api/lessons/challenge-progress/{challenge_id}"""
        print("📊 STEP 5: Testing GET /api/lessons/challenge-progress/challenge_sun_7days...")
        
        try:
            response = self.session.get(f"{BASE_URL}/lessons/challenge-progress/{CHALLENGE_ID}")
            
            if response.status_code == 200:
                data = response.json()
                progress = data.get("progress")
                
                if progress:
                    # Проверяем структуру прогресса
                    has_user_id = "user_id" in progress
                    has_challenge_id = progress.get("challenge_id") == CHALLENGE_ID
                    has_completed_days = "completed_days" in progress
                    has_current_day = "current_day" in progress
                    has_status = progress.get("status") == "active"
                    
                    # Проверяем что день 1 отмечен как выполненный
                    completed_days = progress.get("completed_days", [])
                    day_1_completed = 1 in completed_days
                    
                    if has_user_id and has_challenge_id and has_completed_days and has_current_day and has_status and day_1_completed:
                        self.log_test(
                            "Get Challenge Progress", 
                            True, 
                            f"Progress retrieved: {len(completed_days)} days completed, current day {progress.get('current_day', 0)}, status: {progress.get('status', 'unknown')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Get Challenge Progress", 
                            False, 
                            f"Progress data incomplete: user_id={has_user_id}, challenge_id={has_challenge_id}, completed_days={has_completed_days}, current_day={has_current_day}, status={has_status}, day_1_completed={day_1_completed}"
                        )
                        return False
                else:
                    self.log_test(
                        "Get Challenge Progress", 
                        False, 
                        "No progress data found"
                    )
                    return False
            else:
                self.log_test(
                    "Get Challenge Progress", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.json() if response.content else {}
                )
                return False
                
        except Exception as e:
            self.log_test("Get Challenge Progress", False, f"Error: {str(e)}")
            return False

    def test_submit_quiz(self):
        """Тест 5: POST /api/lessons/submit-quiz"""
        print("🧠 STEP 6: Testing POST /api/lessons/submit-quiz...")
        
        try:
            # Подготавливаем ответы на квиз (правильные ответы для получения хорошего результата)
            quiz_answers = {
                "q1": "a",  # Энергетическое влияние чисел
                "q2": "b",  # Дата рождения
                "q3": "b",  # Планетарная энергия
                "q4": "b",  # 9 планет
                "q5": "b"   # Солнце
            }
            
            form_data = {
                "quiz_id": QUIZ_ID,
                "answers": json.dumps(quiz_answers)
            }
            
            response = self.session.post(f"{BASE_URL}/lessons/submit-quiz", data=form_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем результаты квиза
                score = data.get("score", 0)
                total_questions = data.get("total_questions", 0)
                percentage = data.get("percentage", 0)
                passed = data.get("passed", False)
                results = data.get("results", [])
                
                if score > 0 and total_questions == 5 and percentage >= 60 and passed and len(results) == 5:
                    self.log_test(
                        "Submit Quiz", 
                        True, 
                        f"Quiz completed successfully: {score}/{total_questions} ({percentage}%), passed: {passed}"
                    )
                    return True
                else:
                    self.log_test(
                        "Submit Quiz", 
                        False, 
                        f"Quiz results incomplete: score={score}, total={total_questions}, percentage={percentage}, passed={passed}, results_count={len(results)}"
                    )
                    return False
            else:
                self.log_test(
                    "Submit Quiz", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.json() if response.content else {}
                )
                return False
                
        except Exception as e:
            self.log_test("Submit Quiz", False, f"Error: {str(e)}")
            return False

    def test_add_habit_tracker(self):
        """Тест 6: POST /api/lessons/add-habit-tracker"""
        print("📝 STEP 7: Testing POST /api/lessons/add-habit-tracker...")
        
        try:
            form_data = {
                "lesson_id": LESSON_ID
            }
            
            response = self.session.post(f"{BASE_URL}/lessons/add-habit-tracker", data=form_data)
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                
                if "Трекер привычек" in message and "добавлен" in message:
                    self.log_test(
                        "Add Habit Tracker", 
                        True, 
                        f"Habit tracker added successfully: {message}"
                    )
                    return True
                else:
                    self.log_test(
                        "Add Habit Tracker", 
                        False, 
                        f"Unexpected response message: {message}"
                    )
                    return False
            else:
                self.log_test(
                    "Add Habit Tracker", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.json() if response.content else {}
                )
                return False
                
        except Exception as e:
            self.log_test("Add Habit Tracker", False, f"Error: {str(e)}")
            return False

    def test_update_habit(self):
        """Тест 7: POST /api/lessons/update-habit"""
        print("🔄 STEP 8: Testing POST /api/lessons/update-habit...")
        
        try:
            # Обновляем статус первой привычки
            form_data = {
                "lesson_id": LESSON_ID,
                "habit_name": "Утренняя аффирмация или медитация",
                "completed": True,
                "notes": "Completed morning affirmation practice - felt more confident and energized"
            }
            
            response = self.session.post(f"{BASE_URL}/lessons/update-habit", data=form_data)
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                
                if "Утренняя аффирмация" in message and "обновлена" in message:
                    self.log_test(
                        "Update Habit Status", 
                        True, 
                        f"Habit updated successfully: {message}"
                    )
                    return True
                else:
                    self.log_test(
                        "Update Habit Status", 
                        False, 
                        f"Unexpected response message: {message}"
                    )
                    return False
            else:
                self.log_test(
                    "Update Habit Status", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.json() if response.content else {}
                )
                return False
                
        except Exception as e:
            self.log_test("Update Habit Status", False, f"Error: {str(e)}")
            return False

    def test_get_user_progress(self):
        """Тест 8: GET /api/lessons/user-progress/{lesson_id}"""
        print("📈 STEP 9: Testing GET /api/lessons/user-progress/lesson_numerom_intro...")
        
        try:
            response = self.session.get(f"{BASE_URL}/lessons/user-progress/{LESSON_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру прогресса
                lesson_progress = data.get("lesson_progress", {})
                quiz_results = data.get("quiz_results", [])
                challenge_progress = data.get("challenge_progress", [])
                habit_tracker = data.get("habit_tracker")
                
                # Проверяем что данные присутствуют
                has_lesson_title = "lesson_title" in lesson_progress
                has_exercises_info = "total_exercises" in lesson_progress
                has_quiz_results = len(quiz_results) > 0
                has_challenge_progress = len(challenge_progress) > 0
                has_habit_tracker = habit_tracker is not None
                
                if has_lesson_title and has_exercises_info and has_quiz_results and has_challenge_progress and has_habit_tracker:
                    self.log_test(
                        "Get User Progress", 
                        True, 
                        f"Progress retrieved: lesson '{lesson_progress.get('lesson_title', 'Unknown')}', {lesson_progress.get('total_exercises', 0)} exercises, {len(quiz_results)} quiz results, {len(challenge_progress)} challenges, habit tracker: {'Yes' if habit_tracker else 'No'}"
                    )
                    return True
                else:
                    self.log_test(
                        "Get User Progress", 
                        False, 
                        f"Progress data incomplete: lesson_title={has_lesson_title}, exercises_info={has_exercises_info}, quiz_results={has_quiz_results}, challenge_progress={has_challenge_progress}, habit_tracker={has_habit_tracker}"
                    )
                    return False
            else:
                self.log_test(
                    "Get User Progress", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.json() if response.content else {}
                )
                return False
                
        except Exception as e:
            self.log_test("Get User Progress", False, f"Error: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Запуск полного тестирования всех API endpoints"""
        print("=" * 80)
        print("🚀 COMPREHENSIVE FIRST LESSON API TESTING")
        print("=" * 80)
        print(f"Testing user: {TEST_USER_EMAIL}")
        print(f"Base URL: {BASE_URL}")
        print(f"Lesson ID: {LESSON_ID}")
        print(f"Challenge ID: {CHALLENGE_ID}")
        print(f"Quiz ID: {QUIZ_ID}")
        print("=" * 80)
        print()
        
        # Последовательность тестов
        test_sequence = [
            ("Authentication", self.authenticate),
            ("Get First Lesson", self.test_get_first_lesson),
            ("Start Challenge", self.test_start_challenge),
            ("Complete Challenge Day", self.test_complete_challenge_day),
            ("Get Challenge Progress", self.test_get_challenge_progress),
            ("Submit Quiz", self.test_submit_quiz),
            ("Add Habit Tracker", self.test_add_habit_tracker),
            ("Update Habit", self.test_update_habit),
            ("Get User Progress", self.test_get_user_progress)
        ]
        
        # Выполняем тесты
        for test_name, test_func in test_sequence:
            try:
                success = test_func()
                if not success and test_name == "Authentication":
                    print("❌ Authentication failed - stopping tests")
                    break
                time.sleep(1)  # Небольшая пауза между тестами
            except Exception as e:
                self.log_test(test_name, False, f"Unexpected error: {str(e)}")
        
        # Подсчет результатов
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("=" * 80)
        print("📊 FINAL TEST RESULTS")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Детальные результаты
        print("📋 DETAILED RESULTS:")
        print("-" * 80)
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        print("=" * 80)
        
        # Определяем общий статус
        if success_rate >= 90:
            print("🎉 OVERALL STATUS: EXCELLENT - All FirstLesson API endpoints working correctly!")
            return True
        elif success_rate >= 75:
            print("✅ OVERALL STATUS: GOOD - Most FirstLesson API endpoints working with minor issues")
            return True
        elif success_rate >= 50:
            print("⚠️ OVERALL STATUS: PARTIAL - Some FirstLesson API endpoints have issues")
            return False
        else:
            print("❌ OVERALL STATUS: CRITICAL - Major issues with FirstLesson API endpoints")
            return False

def main():
    """Главная функция для запуска тестов"""
    tester = FirstLessonAPITester()
    
    try:
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Critical error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()