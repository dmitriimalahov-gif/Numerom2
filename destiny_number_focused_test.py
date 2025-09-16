#!/usr/bin/env python3
"""
Focused test for Destiny Number (ЧС) calculation fix with premium user
"""

import requests
import json
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def login_super_admin():
    """Login as super admin to get unlimited credits"""
    login_data = {
        "email": "dmitrii.malahov@gmail.com",
        "password": "756bvy67H"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Super admin login failed: {response.status_code} - {response.text}")
        return None

def test_destiny_number_direct():
    """Test destiny number calculation directly"""
    from backend.numerology import calculate_destiny_number, parse_birth_date
    
    print("🧮 DIRECT FUNCTION TESTING:")
    print("=" * 40)
    
    test_cases = [
        ("10.01.1982", 4),  # 10 + 1 + 1982 = 1993 → 1+9+9+3 = 22 → 2+2 = 4
        ("02.09.1998", 2),  # Should result in 11 → 1+1 = 2
        ("29.11.1992", 4),  # Should result in 22 → 2+2 = 4
    ]
    
    all_passed = True
    
    for birth_date, expected in test_cases:
        day, month, year = parse_birth_date(birth_date)
        actual = calculate_destiny_number(day, month, year)
        
        print(f"📅 {birth_date}: {day} + {month} + {year} = {day + month + year}")
        print(f"   Expected: {expected}, Actual: {actual}")
        
        if actual in [11, 22, 33]:
            print(f"   ❌ CRITICAL: Destiny Number {actual} is master number - should be reduced!")
            all_passed = False
        elif actual == expected:
            print(f"   ✅ CORRECT")
        else:
            print(f"   ⚠️  MISMATCH")
            all_passed = False
        print()
    
    return all_passed

def test_api_endpoint(token):
    """Test API endpoint with super admin token"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🌐 API ENDPOINT TESTING:")
    print("=" * 40)
    
    # Test the main case from review request
    response = requests.post(
        f"{BACKEND_URL}/numerology/personal-numbers",
        json={"birth_date": "10.01.1982"},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        destiny_number = data.get("destiny_number")
        
        print(f"📅 Birth Date: 10.01.1982")
        print(f"📊 Destiny Number: {destiny_number}")
        print(f"📊 Ruling Number: {data.get('ruling_number')}")
        print(f"📊 Helping Mind Number: {data.get('helping_mind_number')}")
        print(f"📊 All numbers: {json.dumps(data, indent=2)}")
        
        if destiny_number == 22:
            print("❌ CRITICAL BUG: Destiny Number is 22 - should be 4!")
            return False
        elif destiny_number == 4:
            print("✅ CORRECT: Destiny Number is properly reduced to 4")
            return True
        else:
            print(f"⚠️  UNEXPECTED: Destiny Number is {destiny_number}")
            return False
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        return False

def main():
    print("🎯 DESTINY NUMBER (ЧС) CALCULATION FOCUSED TEST")
    print("=" * 60)
    print("Review Request: Test that Destiny Number is ALWAYS single digit")
    print("For 10.01.1982: 10 + 1 + 1982 = 1993 → 1+9+9+3 = 22 → 2+2 = 4")
    print()
    
    # Test direct function first
    direct_passed = test_destiny_number_direct()
    
    # Test API endpoint
    token = login_super_admin()
    if token:
        print("✅ Super admin logged in successfully")
        api_passed = test_api_endpoint(token)
    else:
        print("❌ Failed to login as super admin")
        api_passed = False
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print(f"   Direct Function Test: {'✅ PASSED' if direct_passed else '❌ FAILED'}")
    print(f"   API Endpoint Test: {'✅ PASSED' if api_passed else '❌ FAILED'}")
    
    if direct_passed and api_passed:
        print("\n✅ ALL TESTS PASSED: Destiny Number fix is working correctly!")
    else:
        print("\n❌ TESTS FAILED: Destiny Number calculation needs fixing!")
        print("   The calculate_destiny_number function should use reduce_to_single_digit_always")
        print("   which NEVER preserves master numbers 11/22")

if __name__ == "__main__":
    main()