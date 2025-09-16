#!/usr/bin/env python3
"""
Quick test to verify the routing conflict theory
"""

import requests
import json
import uuid

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"

def test_routing_conflict():
    print("🔍 Testing routing conflict theory...")
    
    # Authenticate
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Authentication failed")
        return
    
    token = response.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test the old POST /admin/lessons endpoint (should work)
    print("\n1. Testing old POST /admin/lessons endpoint...")
    old_lesson_data = {
        "id": str(uuid.uuid4()),
        "title": "Old System Test Lesson",
        "description": "Testing old lesson creation",
        "level": 1,
        "order": 1,
        "is_active": True,
        "video_url": "https://example.com/video.mp4"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/admin/lessons", json=old_lesson_data, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test the new POST /admin/lessons/create endpoint (currently failing)
    print("\n2. Testing new POST /admin/lessons/create endpoint...")
    new_lesson_data = {
        "id": str(uuid.uuid4()),
        "title": "New System Test Lesson",
        "module": "test",
        "description": "Testing new lesson creation",
        "is_active": True
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/admin/lessons/create", json=new_lesson_data, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test a completely different path to see if routing works
    print("\n3. Testing GET /admin/lessons (should work)...")
    try:
        response = requests.get(f"{BACKEND_URL}/admin/lessons", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data.get('total_count', 0)} lessons")
    except Exception as e:
        print(f"   Exception: {str(e)}")

if __name__ == "__main__":
    test_routing_conflict()