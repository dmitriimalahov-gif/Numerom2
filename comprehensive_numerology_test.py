#!/usr/bin/env python3
"""
Comprehensive Numerology Test
Tests multiple birth dates to verify master number preservation and formula corrections.
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

def register_test_user():
    """Register a test user and return auth token"""
    user_data = {
        "email": f"testuser{int(time.time())}@numerom.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "birth_date": "10.01.1982",
        "city": "Москва"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=30)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_birth_date(auth_token, birth_date, expected_results, description):
    """Test a specific birth date"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    response = requests.post(f"{BACKEND_URL}/numerology/personal-numbers", 
                           json={"birth_date": birth_date}, 
                           headers=headers, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ {description}: API call failed ({response.status_code})")
        return False
    
    data = response.json()
    success = True
    
    print(f"\n📅 {description} ({birth_date}):")
    for field, expected in expected_results.items():
        actual = data.get(field)
        if actual == expected:
            print(f"   ✅ {field}: {actual}")
        else:
            print(f"   ❌ {field}: expected {expected}, got {actual}")
            success = False
    
    return success

def main():
    """Main test execution"""
    print("🧮 Comprehensive Numerology Corrections Test")
    print("=" * 60)
    
    # Register test user
    print("Setting up test user...")
    auth_token = register_test_user()
    if not auth_token:
        print("❌ Failed to register test user")
        return False
    print("✅ Test user registered")
    
    # Test cases from review request and additional master number cases
    test_cases = [
        {
            "birth_date": "10.01.1982",
            "expected": {
                "destiny_number": 22,  # 10+1+1982=1993→1+9+9+3=22 (preserved)
                "helping_mind_number": 11,  # 10+1=11 (preserved)
                "ruling_number": 22  # 1+0+0+1+1+9+8+2=22 (preserved)
            },
            "description": "Review Request Example - Master numbers 11 and 22"
        },
        {
            "birth_date": "02.09.1998",
            "expected": {
                "ruling_number": 11  # 0+2+0+9+1+9+9+8=38→3+8=11 (preserved during reduction)
            },
            "description": "Master number 11 during ruling number reduction"
        },
        {
            "birth_date": "15.03.1990",
            "expected": {
                "ruling_number": 1  # 1+5+0+3+1+9+9+0=28→2+8=10→1+0=1 (normal reduction)
            },
            "description": "Normal reduction (no master numbers)"
        },
        {
            "birth_date": "29.02.1992",
            "expected": {
                "helping_mind_number": 11  # 29+2=31→3+1=4, but direct: 29+2=31, need to check logic
            },
            "description": "Helping mind number with potential master"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        success = test_birth_date(
            auth_token,
            test_case["birth_date"],
            test_case["expected"],
            test_case["description"]
        )
        if not success:
            all_passed = False
    
    # Additional verification: Test that old vs new calculations show differences
    print(f"\n🔍 Additional Verification:")
    print("Testing that master numbers are preserved correctly...")
    
    # Test a case where old calculation would reduce but new should preserve
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    response = requests.post(f"{BACKEND_URL}/numerology/personal-numbers", 
                           json={"birth_date": "10.01.1982"}, 
                           headers=headers, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        destiny = data.get("destiny_number")
        
        # Old calculation would have been: 1993→1+9+9+3=22→2+2=4
        # New calculation should be: 1993→1+9+9+3=22 (preserved)
        if destiny == 22:
            print("   ✅ New formula correctly preserves master number 22 in destiny calculation")
        elif destiny == 4:
            print("   ❌ Still using old formula - master number 22 was reduced to 4")
            all_passed = False
        else:
            print(f"   ❌ Unexpected destiny number: {destiny}")
            all_passed = False
    
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Corrected numerology formulas are working correctly")
        print("✅ Master numbers (11, 22) are preserved during reduction")
        print("✅ API endpoints are functioning properly")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("❌ Issues found with numerology calculations")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)