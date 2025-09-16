#!/usr/bin/env python3
"""
Debug Learning Management Test
"""

import requests
import json
import time

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def test_learning_debug():
    # Register a user first
    user_data = {
        "email": f"learninguser{int(time.time())}@numerom.com",
        "password": "LearningPass123!",
        "full_name": "Learning User",
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
    
    # Test learning levels endpoint
    print("Testing learning levels endpoint...")
    learning_response = requests.get(
        f"{BACKEND_URL}/learning/levels",
        headers=headers
    )
    
    print(f"Learning Status: {learning_response.status_code}")
    print(f"Learning Response: {learning_response.text}")
    
    # Make user admin and test admin endpoints
    admin_response = requests.post(
        f"{BACKEND_URL}/admin/make-admin/{user_id}",
        headers=headers
    )
    
    print(f"Admin Status: {admin_response.status_code}")
    print(f"Admin Response: {admin_response.text}")
    
    # Test admin lessons endpoint
    print("Testing admin lessons endpoint...")
    admin_lessons_response = requests.get(
        f"{BACKEND_URL}/admin/lessons",
        headers=headers
    )
    
    print(f"Admin Lessons Status: {admin_lessons_response.status_code}")
    print(f"Admin Lessons Response: {admin_lessons_response.text}")

if __name__ == "__main__":
    test_learning_debug()