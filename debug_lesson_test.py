#!/usr/bin/env python3
"""
Debug Test for Lesson Management Endpoints
Testing the actual endpoint availability and structure
"""

import requests
import json
import uuid

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"

def test_authentication():
    """Test authentication"""
    print("🔐 Testing authentication...")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            user_info = data["user"]
            print(f"✅ Authenticated as {user_info['email']}")
            print(f"   Credits: {user_info.get('credits_remaining', 0)}")
            print(f"   Super Admin: {user_info.get('is_super_admin', False)}")
            return token
        else:
            print(f"❌ Authentication failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return None

def test_endpoint_availability(token):
    """Test if endpoints are available"""
    print("\n🔍 Testing endpoint availability...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test existing GET endpoint
    try:
        response = requests.get(f"{BACKEND_URL}/admin/lessons", headers=headers)
        print(f"GET /admin/lessons: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data.get('total_count', 0)} lessons")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test create endpoint with OPTIONS first
    try:
        response = requests.options(f"{BACKEND_URL}/admin/lessons/create", headers=headers)
        print(f"OPTIONS /admin/lessons/create: {response.status_code}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test create endpoint with minimal data
    test_lesson = {
        "id": str(uuid.uuid4()),
        "title": "Debug Test Lesson",
        "module": "test",
        "description": "Test lesson for debugging",
        "is_active": True
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/admin/lessons/create", json=test_lesson, headers=headers)
        print(f"POST /admin/lessons/create: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Create endpoint working")
            return test_lesson["id"]
        else:
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"   Exception: {str(e)}")
        return None

def test_get_lesson(token, lesson_id):
    """Test get lesson by ID"""
    if not lesson_id:
        print("\n❌ No lesson ID to test get endpoint")
        return
        
    print(f"\n📖 Testing GET lesson by ID: {lesson_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BACKEND_URL}/admin/lessons/{lesson_id}", headers=headers)
        print(f"GET /admin/lessons/{lesson_id}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            lesson = data.get('lesson', {})
            print(f"   ✅ Lesson found: {lesson.get('title', 'No title')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")

def test_content_update(token, lesson_id):
    """Test content update with correct structure"""
    if not lesson_id:
        print("\n❌ No lesson ID to test content update")
        return
        
    print(f"\n✏️ Testing content update for lesson: {lesson_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test the expected structure based on server.py code
    content_update = {
        "section": "theory",
        "field": "what_is_topic",
        "value": "UPDATED: Debug test content"
    }
    
    try:
        response = requests.put(f"{BACKEND_URL}/admin/lessons/{lesson_id}/content", json=content_update, headers=headers)
        print(f"PUT /admin/lessons/{lesson_id}/content: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Content update working")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")

def test_video_upload(token, lesson_id):
    """Test video upload"""
    if not lesson_id:
        print("\n❌ No lesson ID to test video upload")
        return
        
    print(f"\n🎥 Testing video upload for lesson: {lesson_id}")
    
    headers = {
        "Authorization": f"Bearer {token}"
        # Don't set Content-Type for multipart
    }
    
    # Create a small dummy video file
    dummy_video_content = b'DUMMY_VIDEO_DATA' * 100
    
    files = {
        'file': ('test_video.mp4', dummy_video_content, 'video/mp4')
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/admin/lessons/{lesson_id}/upload-video", files=files, headers=headers)
        print(f"POST /admin/lessons/{lesson_id}/upload-video: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Video uploaded: {data.get('file_id', 'No file ID')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")

def test_pdf_upload(token, lesson_id):
    """Test PDF upload"""
    if not lesson_id:
        print("\n❌ No lesson ID to test PDF upload")
        return
        
    print(f"\n📄 Testing PDF upload for lesson: {lesson_id}")
    
    headers = {
        "Authorization": f"Bearer {token}"
        # Don't set Content-Type for multipart
    }
    
    # Create a small dummy PDF file
    dummy_pdf_content = b'%PDF-1.4\nDUMMY_PDF_DATA' * 50
    
    files = {
        'file': ('test_document.pdf', dummy_pdf_content, 'application/pdf')
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/admin/lessons/{lesson_id}/upload-pdf", files=files, headers=headers)
        print(f"POST /admin/lessons/{lesson_id}/upload-pdf: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ PDF uploaded: {data.get('file_id', 'No file ID')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")

def cleanup_test_lesson(token, lesson_id):
    """Clean up test lesson"""
    if not lesson_id:
        return
        
    print(f"\n🗑️ Cleaning up test lesson: {lesson_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(f"{BACKEND_URL}/admin/lessons/{lesson_id}", headers=headers)
        print(f"DELETE /admin/lessons/{lesson_id}: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Test lesson cleaned up")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")

def main():
    print("🚀 Starting Debug Test for Lesson Management Endpoints")
    print("=" * 60)
    
    # Authenticate
    token = test_authentication()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Test endpoint availability and create lesson
    lesson_id = test_endpoint_availability(token)
    
    # Test other endpoints
    test_get_lesson(token, lesson_id)
    test_content_update(token, lesson_id)
    test_video_upload(token, lesson_id)
    test_pdf_upload(token, lesson_id)
    
    # Cleanup
    cleanup_test_lesson(token, lesson_id)
    
    print("\n" + "=" * 60)
    print("🏁 Debug test completed")

if __name__ == "__main__":
    main()