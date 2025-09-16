#!/usr/bin/env python3
"""
Debug script to test access control issues
"""

import requests
import json
import time

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def test_regular_user_access():
    # Register a regular user
    user_data = {
        "email": f"debug_user_{int(time.time())}@test.com",
        "password": "TestPass123!",
        "full_name": "Debug Test User",
        "birth_date": "10.05.1995",
        "city": "Москва"
    }
    
    print("Registering regular user...")
    response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=30)
    print(f"Registration status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        print(f"Got token: {token[:20]}...")
        
        # Test access to admin endpoint
        print("\nTesting access to /admin/users...")
        headers = {"Authorization": f"Bearer {token}"}
        admin_response = requests.get(f"{BACKEND_URL}/admin/users", headers=headers, timeout=30)
        print(f"Admin endpoint status: {admin_response.status_code}")
        print(f"Admin endpoint response: {admin_response.text[:200]}")
        
        # Test access to regular endpoint
        print("\nTesting access to /user/profile...")
        profile_response = requests.get(f"{BACKEND_URL}/user/profile", headers=headers, timeout=30)
        print(f"Profile endpoint status: {profile_response.status_code}")
        print(f"Profile response: {profile_response.text[:200]}")
        
    else:
        print(f"Registration failed: {response.text}")

if __name__ == "__main__":
    test_regular_user_access()