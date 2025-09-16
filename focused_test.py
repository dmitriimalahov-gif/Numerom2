#!/usr/bin/env python3
"""
Focused test for NUMEROM Enhanced Features
"""

import requests
import json
import time
from datetime import datetime

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def create_test_user():
    """Create a fresh test user"""
    timestamp = int(time.time())
    user_data = {
        "email": f"testuser{timestamp}@numerom.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "birth_date": "15.03.1990",
        "city": "Москва"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data)
    if response.status_code == 200:
        data = response.json()
        return data["access_token"], user_data["email"]
    return None, None

def test_enhanced_features():
    """Test the enhanced features"""
    print("🔥 FOCUSED TEST: Enhanced NUMEROM Features")
    print("=" * 50)
    
    # Create test user and get token
    token, email = create_test_user()
    if not token:
        print("❌ Failed to create test user")
        return
    
    print(f"✅ Created test user: {email}")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Test 1: Vedic Time Daily Schedule (HIGH PRIORITY)
    print("\n🎯 Testing Vedic Time Daily Schedule...")
    response = requests.get(f"{BACKEND_URL}/vedic-time/daily-schedule?city=Moscow&date=2025-01-15", headers=headers)
    if response.status_code == 200:
        data = response.json()
        if all(field in data for field in ["city", "inauspicious_periods", "auspicious_periods", "planetary_hours"]):
            if "rahu_kaal" in data["inauspicious_periods"] and "abhijit_muhurta" in data["auspicious_periods"]:
                print("✅ Vedic Time Daily Schedule - Working with Sanskrit terminology")
            else:
                print("❌ Vedic Time Daily Schedule - Missing Sanskrit periods")
        else:
            print("❌ Vedic Time Daily Schedule - Missing required fields")
    else:
        print(f"❌ Vedic Time Daily Schedule - HTTP {response.status_code}: {response.text}")
    
    # Test 2: Enhanced Numerology Full Analysis (HIGH PRIORITY)
    print("\n🎯 Testing Enhanced Numerology Full Analysis...")
    response = requests.post(f"{BACKEND_URL}/numerology/enhanced/full-analysis", 
                           json={"name": "Александр Иванов"}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "enhanced_square" in data:
            enhanced_square = data["enhanced_square"]
            if "planet_positions" in enhanced_square and "method" in enhanced_square:
                method = enhanced_square.get("method", "")
                if "Ведическая система" in method:
                    print("✅ Enhanced Numerology Full Analysis - Working with Vedic system")
                else:
                    print(f"❌ Enhanced Numerology Full Analysis - Wrong method: {method}")
            else:
                print("❌ Enhanced Numerology Full Analysis - Missing enhanced square details")
        else:
            print("❌ Enhanced Numerology Full Analysis - Missing enhanced_square")
    else:
        print(f"❌ Enhanced Numerology Full Analysis - HTTP {response.status_code}: {response.text}")
    
    # Test 3: Planetary Route API (HIGH PRIORITY)
    print("\n🎯 Testing Planetary Route API...")
    response = requests.get(f"{BACKEND_URL}/vedic-time/planetary-route?date=2025-01-20", headers=headers)
    if response.status_code == 200:
        data = response.json()
        required_fields = ["date", "city", "best_activity_hours", "avoid_periods", "favorable_period"]
        if all(field in data for field in required_fields):
            avoid_periods = data.get("avoid_periods", {})
            if "rahu_kaal" in avoid_periods and "gulika_kaal" in avoid_periods:
                print("✅ Planetary Route API - Working with avoid periods and recommendations")
            else:
                print("❌ Planetary Route API - Missing avoid periods")
        else:
            missing = [f for f in required_fields if f not in data]
            print(f"❌ Planetary Route API - Missing fields: {missing}")
    else:
        print(f"❌ Planetary Route API - HTTP {response.status_code}: {response.text}")
    
    # Test 4: City Change API (MEDIUM PRIORITY)
    print("\n📋 Testing City Change API...")
    response = requests.post(f"{BACKEND_URL}/user/change-city", 
                           json={"city": "Mumbai"}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "city" in data and data["city"] == "Mumbai":
            print("✅ City Change API - Working correctly")
        else:
            print(f"❌ City Change API - Wrong response: {data}")
    else:
        print(f"❌ City Change API - HTTP {response.status_code}: {response.text}")
    
    # Test 5: Lesson Descriptions API (MEDIUM PRIORITY)
    print("\n📋 Testing Lesson Descriptions API...")
    response = requests.get(f"{BACKEND_URL}/learning/lessons/descriptions", headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "lessons" in data and "methodology_source" in data:
            lessons = data["lessons"]
            methodology = data["methodology_source"]
            if isinstance(lessons, list) and len(lessons) > 0 and "Ведическая нумерология" in methodology:
                print(f"✅ Lesson Descriptions API - Retrieved {len(lessons)} lessons from Vedic methodology")
            else:
                print(f"❌ Lesson Descriptions API - Invalid lessons or methodology: {methodology}")
        else:
            print("❌ Lesson Descriptions API - Missing required fields")
    else:
        print(f"❌ Lesson Descriptions API - HTTP {response.status_code}: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 Focused test completed!")

if __name__ == "__main__":
    test_enhanced_features()