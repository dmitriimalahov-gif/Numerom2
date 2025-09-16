#!/usr/bin/env python3
"""
Video Upload Functionality Testing
Tests the video upload for lessons functionality
"""

import requests
import json
import io
import time

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def test_video_upload_functionality():
    print("🎥 VIDEO UPLOAD FUNCTIONALITY TESTING")
    print("=" * 50)
    
    results = []
    
    # 1. Login as Super Admin
    print("\n1. Logging in as Super Admin...")
    super_admin_creds = {
        "email": "dmitrii.malahov@gmail.com",
        "password": "756bvy67H"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=super_admin_creds, timeout=30)
    if response.status_code != 200:
        print(f"❌ Super admin login failed: {response.text}")
        return []
    
    data = response.json()
    super_admin_token = data["access_token"]
    print("✅ Super admin logged in successfully")
    
    # 2. Create a test lesson first
    print("\n2. Creating a test lesson...")
    headers = {"Authorization": f"Bearer {super_admin_token}"}
    lesson_data = {
        "id": f"test_lesson_{int(time.time())}",
        "title": "Test Video Lesson",
        "description": "Test lesson for video upload",
        "video_url": "https://example.com/placeholder.mp4",
        "level": 1,
        "order": 1,
        "duration_minutes": 30,
        "is_active": True
    }
    
    response = requests.post(f"{BACKEND_URL}/admin/lessons", json=lesson_data, headers=headers, timeout=30)
    if response.status_code == 200:
        lesson_id = lesson_data["id"]
        print(f"✅ Test lesson created: {lesson_id}")
        results.append(("Create Test Lesson", True))
    else:
        print(f"❌ Failed to create test lesson: {response.status_code} - {response.text}")
        results.append(("Create Test Lesson", False))
        return results
    
    # 3. Test video upload endpoint exists and requires super admin
    print("\n3. Testing video upload endpoint access control...")
    
    # First test with regular user (should fail)
    regular_user_data = {
        "email": f"regular_{int(time.time())}@test.com",
        "password": "TestPass123!",
        "full_name": "Regular User",
        "birth_date": "10.05.1995",
        "city": "Москва"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=regular_user_data, timeout=30)
    if response.status_code == 200:
        regular_token = response.json()["access_token"]
        
        # Try to upload with regular user
        mock_video_content = b"MOCK_VIDEO_DATA" * 100
        files = {'file': ('test_video.mp4', io.BytesIO(mock_video_content), 'video/mp4')}
        regular_headers = {"Authorization": f"Bearer {regular_token}"}
        
        response = requests.post(f"{BACKEND_URL}/admin/lessons/{lesson_id}/upload-video", 
                               files=files, headers=regular_headers, timeout=30)
        
        if response.status_code == 403:
            print("✅ Regular user correctly blocked from video upload")
            results.append(("Video Upload Access Control", True))
        else:
            print(f"❌ Regular user should be blocked but got: {response.status_code}")
            results.append(("Video Upload Access Control", False))
    else:
        print("❌ Failed to create regular user for testing")
        results.append(("Video Upload Access Control", False))
    
    # 4. Test video upload with super admin
    print("\n4. Testing video upload with super admin...")
    
    mock_video_content = b"MOCK_VIDEO_DATA_FOR_TESTING" * 200  # Create larger mock file
    files = {'file': ('test_video.mp4', io.BytesIO(mock_video_content), 'video/mp4')}
    
    response = requests.post(f"{BACKEND_URL}/admin/lessons/{lesson_id}/upload-video", 
                           files=files, headers=headers, timeout=60)
    
    if response.status_code == 200:
        upload_data = response.json()
        if upload_data.get("success"):
            video_url = upload_data.get("video_url", "")
            video_id = upload_data.get("video_id", "")
            print(f"✅ Video uploaded successfully")
            print(f"   Video URL: {video_url}")
            print(f"   Video ID: {video_id}")
            results.append(("Video Upload Success", True))
            
            # Test video retrieval
            if video_id:
                print("\n5. Testing video retrieval...")
                response = requests.get(f"{BACKEND_URL}/video/{video_id}", timeout=30)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    print(f"✅ Video retrieved successfully")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Content-Length: {content_length} bytes")
                    results.append(("Video Retrieval", True))
                else:
                    print(f"❌ Failed to retrieve video: {response.status_code}")
                    results.append(("Video Retrieval", False))
        else:
            print(f"❌ Video upload response indicates failure: {upload_data}")
            results.append(("Video Upload Success", False))
    else:
        print(f"❌ Video upload failed: {response.status_code}")
        if response.text:
            print(f"   Error: {response.text}")
        results.append(("Video Upload Success", False))
    
    # 5. Test file validation
    print("\n6. Testing file format validation...")
    
    # Test with invalid file type
    invalid_file_content = b"This is not a video file"
    files = {'file': ('test_file.txt', io.BytesIO(invalid_file_content), 'text/plain')}
    
    response = requests.post(f"{BACKEND_URL}/admin/lessons/{lesson_id}/upload-video", 
                           files=files, headers=headers, timeout=30)
    
    if response.status_code == 400:
        error_text = response.text.lower()
        if "формат" in error_text or "format" in error_text:
            print("✅ Invalid file format correctly rejected")
            results.append(("File Format Validation", True))
        else:
            print(f"❌ Wrong error message for invalid format: {response.text}")
            results.append(("File Format Validation", False))
    else:
        print(f"❌ Invalid file should be rejected but got: {response.status_code}")
        results.append(("File Format Validation", False))
    
    # Print Summary
    print("\n" + "=" * 50)
    print("📊 VIDEO UPLOAD TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Show results
    print("\n📋 DETAILED RESULTS:")
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
    
    return results

if __name__ == "__main__":
    test_video_upload_functionality()