#!/usr/bin/env python3
"""
Quick debug test for specific endpoints
"""

import requests
import json
import time

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def get_auth_token():
    """Get auth token by registering a user"""
    user_data = {
        "email": f"debuguser{int(time.time())}@numerom.com",
        "password": "DebugPass123!",
        "full_name": "Debug User",
        "birth_date": "15.03.1990",
        "city": "Москва"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"Registration failed: {response.status_code} - {response.text}")
        return None

def test_pythagorean_square(token):
    """Test Pythagorean Square endpoint"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(f"{BACKEND_URL}/numerology/pythagorean-square", headers=headers)
    print(f"Pythagorean Square: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
    else:
        data = response.json()
        print(f"Success: additional_numbers = {data.get('additional_numbers')}")

def test_vedic_time(token):
    """Test Vedic Time endpoint"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.get(f"{BACKEND_URL}/vedic-time/daily-schedule?date=2025-03-15&city=Москва", headers=headers)
    print(f"Vedic Time: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
    else:
        data = response.json()
        print(f"Success: has rahu_kaal = {'rahu_kaal' in data.get('inauspicious_periods', {})}")

if __name__ == "__main__":
    print("Getting auth token...")
    token = get_auth_token()
    if token:
        print("Testing endpoints...")
        test_pythagorean_square(token)
        test_vedic_time(token)
    else:
        print("Failed to get auth token")