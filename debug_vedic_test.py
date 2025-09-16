#!/usr/bin/env python3
"""
Debug Vedic Numerology Test
"""

import requests
import json
import time

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def test_vedic_debug():
    # Register a user first
    user_data = {
        "email": f"debuguser{int(time.time())}@numerom.com",
        "password": "DebugPass123!",
        "full_name": "Debug User",
        "birth_date": "15.03.1990"
    }
    
    # Register
    response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"Registration failed: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Test Vedic endpoint
    print("Testing Vedic numerology endpoint...")
    vedic_response = requests.post(
        f"{BACKEND_URL}/numerology/vedic/comprehensive",
        json={"name": "Debug Test"},
        headers=headers
    )
    
    print(f"Status: {vedic_response.status_code}")
    print(f"Response: {vedic_response.text}")

if __name__ == "__main__":
    test_vedic_debug()