#!/usr/bin/env python3
"""
API Numerology Test
Tests the numerology API endpoint with the corrected formulas.
"""

import requests
import json
import time

# Get backend URL from environment
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=')[1].strip() + '/api'
            break

def test_api_numerology():
    """Test the API numerology endpoint"""
    print("🌐 Testing NUMEROM API Numerology Endpoint")
    print("=" * 50)
    
    # Register a test user
    user_data = {
        "email": f"testuser{int(time.time())}@numerom.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "birth_date": "10.01.1982",
        "city": "Москва"
    }
    
    print("1. Registering test user...")
    register_response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=30)
    
    if register_response.status_code != 200:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False
    
    auth_data = register_response.json()
    auth_token = auth_data.get("access_token")
    
    if not auth_token:
        print("❌ No auth token received")
        return False
    
    print("✅ User registered successfully")
    
    # Test personal numbers calculation
    print("\n2. Testing personal numbers calculation...")
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    # Test with the specific birth date from review request
    numerology_response = requests.post(f"{BACKEND_URL}/numerology/personal-numbers", 
                                      json={"birth_date": "10.01.1982"}, 
                                      headers=headers, timeout=30)
    
    if numerology_response.status_code != 200:
        print(f"❌ Numerology calculation failed: {numerology_response.status_code}")
        print(f"Response: {numerology_response.text}")
        return False
    
    data = numerology_response.json()
    print("✅ Personal numbers calculated successfully")
    
    # Verify the calculations
    print("\n3. Verifying calculations...")
    expected_results = {
        "destiny_number": 22,  # 10+1+1982=1993→1+9+9+3=22 (preserved)
        "helping_mind_number": 11,  # 10+1=11 (preserved)
        "ruling_number": 22  # 1+0+0+1+1+9+8+2=22 (preserved)
    }
    
    all_correct = True
    for field, expected in expected_results.items():
        actual = data.get(field)
        if actual == expected:
            print(f"✅ {field}: {actual} (correct)")
        else:
            print(f"❌ {field}: expected {expected}, got {actual}")
            all_correct = False
    
    # Show all calculated numbers
    print("\n4. All calculated numbers:")
    print(f"   Soul Number: {data.get('soul_number')}")
    print(f"   Mind Number: {data.get('mind_number')}")
    print(f"   Destiny Number: {data.get('destiny_number')}")
    print(f"   Helping Mind Number: {data.get('helping_mind_number')}")
    print(f"   Wisdom Number: {data.get('wisdom_number')}")
    print(f"   Ruling Number: {data.get('ruling_number')}")
    print(f"   Birth Weekday: {data.get('birth_weekday')}")
    
    # Show planetary strength
    planetary_strength = data.get('planetary_strength', {})
    if planetary_strength:
        print(f"\n5. Planetary Strength:")
        for planet, strength in planetary_strength.items():
            print(f"   {planet}: {strength}")
    
    print("\n" + "=" * 50)
    print(f"🎯 API Test Result: {'PASSED' if all_correct else 'FAILED'}")
    
    return all_correct

if __name__ == "__main__":
    success = test_api_numerology()
    exit(0 if success else 1)