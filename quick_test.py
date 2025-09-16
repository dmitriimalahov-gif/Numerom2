#!/usr/bin/env python3
"""
Quick test for Vedic time endpoints
"""

import requests
import json

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

# First register and get token
user_data = {
    "email": "quicktest@numerom.com",
    "password": "SecurePass123!",
    "full_name": "Quick Test",
    "birth_date": "15.03.1990",
    "city": "Москва"
}

print("Registering user...")
response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=30)
if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"✅ Got token: {token[:20]}...")
    
    # Test vedic time endpoint
    print("\nTesting Vedic time endpoint...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/vedic-time/daily-schedule?city=Москва&date=2025-01-15", 
                              headers=headers, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('city', 'No city')} - {data.get('date', 'No date')}")
        else:
            print(f"❌ Error: {response.text}")
    except requests.exceptions.Timeout:
        print("❌ Timeout error")
    except Exception as e:
        print(f"❌ Exception: {e}")
        
    # Test personal numbers endpoint
    print("\nTesting personal numbers endpoint...")
    try:
        response = requests.post(f"{BACKEND_URL}/numerology/personal-numbers", 
                               headers=headers, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Got {len(data)} fields")
        else:
            print(f"❌ Error: {response.text}")
    except requests.exceptions.Timeout:
        print("❌ Timeout error")
    except Exception as e:
        print(f"❌ Exception: {e}")
        
else:
    print(f"❌ Registration failed: {response.text}")