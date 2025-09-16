#!/usr/bin/env python3
"""
Debug specific endpoint issues
"""

import requests
import json
import uuid
import tempfile
import os

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"

def authenticate():
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def debug_get_lesson():
    print("🔍 Debugging GET lesson endpoint...")
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First create a lesson
    lesson_data = {
        "id": str(uuid.uuid4()),
        "title": "Debug Test Lesson",
        "module": "numerology",
        "description": "Debug test lesson",
        "points_required": 5,
        "is_active": True,
        "content": {
            "theory": {
                "what_is_topic": "Test topic",
                "main_story": "Test story",
                "key_concepts": "Test concepts",
                "practical_applications": "Test applications"
            }
        }
    }
    
    # Create lesson
    response = requests.post(f"{BACKEND_URL}/admin/lessons/create", json=lesson_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create lesson: {response.text}")
        return
    
    lesson_id = lesson_data["id"]
    print(f"✅ Created lesson with ID: {lesson_id}")
    
    # Get lesson
    response = requests.get(f"{BACKEND_URL}/admin/lessons/{lesson_id}", headers=headers)
    print(f"GET response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("📄 Actual lesson data structure:")
        print(json.dumps(data, indent=2, default=str))
        
        # Check what fields are present
        lesson = data.get('lesson', {})
        print(f"\n🔍 Field analysis:")
        print(f"   title: {lesson.get('title')} (expected: {lesson_data['title']})")
        print(f"   module: {lesson.get('module')} (expected: {lesson_data['module']})")
        print(f"   content exists: {'content' in lesson}")
        
    else:
        print(f"❌ Failed to get lesson: {response.text}")
    
    # Cleanup
    requests.delete(f"{BACKEND_URL}/admin/lessons/{lesson_id}", headers=headers)

def debug_content_update():
    print("\n🔍 Debugging content update endpoint...")
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a lesson first
    lesson_data = {
        "id": str(uuid.uuid4()),
        "title": "Content Update Test",
        "module": "numerology",
        "description": "Test lesson for content update",
        "is_active": True,
        "content": {
            "theory": {
                "what_is_topic": "Original topic"
            }
        }
    }
    
    response = requests.post(f"{BACKEND_URL}/admin/lessons/create", json=lesson_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create lesson: {response.text}")
        return
    
    lesson_id = lesson_data["id"]
    print(f"✅ Created lesson with ID: {lesson_id}")
    
    # Test content update with correct structure
    content_update = {
        "section": "theory",
        "field": "what_is_topic",
        "value": "UPDATED: New topic content"
    }
    
    response = requests.put(f"{BACKEND_URL}/admin/lessons/{lesson_id}/content", json=content_update, headers=headers)
    print(f"Content update status: {response.status_code}")
    print(f"Content update response: {response.text}")
    
    # Cleanup
    requests.delete(f"{BACKEND_URL}/admin/lessons/{lesson_id}", headers=headers)

def debug_file_uploads():
    print("\n🔍 Debugging file upload endpoints...")
    
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
        # Don't set Content-Type for multipart
    }
    
    # Create a lesson first
    lesson_data = {
        "id": str(uuid.uuid4()),
        "title": "File Upload Test",
        "module": "numerology",
        "description": "Test lesson for file uploads",
        "is_active": True
    }
    
    response = requests.post(f"{BACKEND_URL}/admin/lessons/create", json=lesson_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create lesson: {response.text}")
        return
    
    lesson_id = lesson_data["id"]
    print(f"✅ Created lesson with ID: {lesson_id}")
    
    # Test video upload
    print("\n🎥 Testing video upload...")
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        temp_file.write(b'DUMMY_VIDEO_DATA' * 100)
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, 'rb') as video_file:
            files = {
                'file': ('test_video.mp4', video_file, 'video/mp4')
            }
            
            response = requests.post(
                f"{BACKEND_URL}/admin/lessons/{lesson_id}/upload-video",
                files=files,
                headers=headers
            )
            print(f"Video upload status: {response.status_code}")
            print(f"Video upload response: {response.text}")
    finally:
        os.unlink(temp_file_path)
    
    # Test PDF upload
    print("\n📄 Testing PDF upload...")
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_file.write(b'%PDF-1.4\nDUMMY_PDF_DATA' * 50)
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, 'rb') as pdf_file:
            files = {
                'file': ('test_document.pdf', pdf_file, 'application/pdf')
            }
            
            response = requests.post(
                f"{BACKEND_URL}/admin/lessons/{lesson_id}/upload-pdf",
                files=files,
                headers=headers
            )
            print(f"PDF upload status: {response.status_code}")
            print(f"PDF upload response: {response.text}")
    finally:
        os.unlink(temp_file_path)
    
    # Cleanup
    requests.delete(f"{BACKEND_URL}/admin/lessons/{lesson_id}", headers=headers)

if __name__ == "__main__":
    debug_get_lesson()
    debug_content_update()
    debug_file_uploads()