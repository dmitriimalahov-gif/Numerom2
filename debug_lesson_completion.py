#!/usr/bin/env python3
"""
Debug Lesson Completion Test
"""

import requests
import json
import time

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def test_lesson_completion():
    # Register a user first
    user_data = {
        "email": f"lessonuser{int(time.time())}@numerom.com",
        "password": "LessonPass123!",
        "full_name": "Lesson User",
        "birth_date": "15.03.1990"
    }
    
    # Register
    response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"Registration failed: {response.text}")
        return
    
    token = response.json()["access_token"]
    user_id = response.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Make user admin
    admin_response = requests.post(
        f"{BACKEND_URL}/admin/make-admin/{user_id}",
        headers=headers
    )
    
    if admin_response.status_code != 200:
        print(f"Admin creation failed: {admin_response.text}")
        return
    
    # Create a lesson
    lesson_data = {
        "title": "Test Lesson for Completion",
        "description": "Test lesson description",
        "video_url": "https://example.com/test-lesson.mp4",
        "duration_minutes": 10,
        "level": 1,
        "order": 1,
        "prerequisites": [],
        "is_active": True
    }
    
    create_response = requests.post(
        f"{BACKEND_URL}/admin/lessons",
        json=lesson_data,
        headers=headers
    )
    
    print(f"Create Lesson Status: {create_response.status_code}")
    print(f"Create Lesson Response: {create_response.text}")
    
    if create_response.status_code == 200:
        lesson_id = create_response.json().get("lesson_id")
        
        # Try to complete the lesson
        complete_response = requests.post(
            f"{BACKEND_URL}/learning/complete-lesson/{lesson_id}?watch_time=10&quiz_score=85",
            headers=headers
        )
        
        print(f"Complete Lesson Status: {complete_response.status_code}")
        print(f"Complete Lesson Response: {complete_response.text}")

if __name__ == "__main__":
    test_lesson_completion()