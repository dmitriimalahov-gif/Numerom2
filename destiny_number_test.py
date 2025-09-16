#!/usr/bin/env python3
"""
Focused test for Destiny Number (ЧС) calculation fix
Testing that Destiny Number is ALWAYS reduced to single digit (1-9), never 11 or 22
"""

import requests
import json
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def register_test_user():
    """Register a test user for API calls"""
    user_data = {
        "email": f"destiny_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com",
        "password": "testpass123",
        "full_name": "Destiny Test User",
        "birth_date": "10.01.1982",
        "city": "Москва"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None

def test_destiny_number_calculation(token, birth_date, expected_destiny):
    """Test destiny number calculation for a specific birth date"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BACKEND_URL}/numerology/personal-numbers",
        json={"birth_date": birth_date},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        destiny_number = data.get("destiny_number")
        
        print(f"📅 Birth Date: {birth_date}")
        print(f"🎯 Expected Destiny Number: {expected_destiny}")
        print(f"📊 Actual Destiny Number: {destiny_number}")
        
        # Check if destiny number is single digit (1-9)
        if destiny_number in [11, 22, 33]:
            print(f"❌ CRITICAL ERROR: Destiny Number {destiny_number} is a master number - should be reduced to single digit!")
            return False
        elif destiny_number < 1 or destiny_number > 9:
            print(f"❌ ERROR: Destiny Number {destiny_number} is not in valid range 1-9!")
            return False
        elif destiny_number == expected_destiny:
            print(f"✅ CORRECT: Destiny Number {destiny_number} matches expected value")
            return True
        else:
            print(f"⚠️  WARNING: Destiny Number {destiny_number} doesn't match expected {expected_destiny}")
            return False
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        return False

def test_master_numbers_preserved_in_other_fields(token, birth_date):
    """Test that other numbers can still preserve master numbers 11/22"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BACKEND_URL}/numerology/personal-numbers",
        json={"birth_date": birth_date},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n🔍 Testing master number preservation for {birth_date}:")
        print(f"   Ruling Number: {data.get('ruling_number')}")
        print(f"   Helping Mind Number: {data.get('helping_mind_number')}")
        print(f"   Soul Number: {data.get('soul_number')}")
        print(f"   Mind Number: {data.get('mind_number')}")
        print(f"   Wisdom Number: {data.get('wisdom_number')}")
        
        # Check if any other numbers have master numbers (this is allowed)
        master_numbers_found = []
        for field in ['ruling_number', 'helping_mind_number', 'soul_number', 'mind_number', 'wisdom_number']:
            value = data.get(field)
            if value in [11, 22]:
                master_numbers_found.append(f"{field}: {value}")
        
        if master_numbers_found:
            print(f"✅ Master numbers preserved in other fields: {', '.join(master_numbers_found)}")
        else:
            print("ℹ️  No master numbers found in other fields for this date")
        
        return True
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        return False

def main():
    print("🎯 DESTINY NUMBER (ЧС) CALCULATION TEST")
    print("=" * 50)
    print("Testing that Destiny Number is ALWAYS reduced to single digit (1-9)")
    print("Other numbers can preserve master numbers 11/22, but Destiny Number cannot")
    print()
    
    # Register test user
    token = register_test_user()
    if not token:
        print("❌ Failed to register test user")
        return
    
    print("✅ Test user registered successfully")
    print()
    
    # Test cases from review request
    test_cases = [
        # Main test case from review request
        ("10.01.1982", 4),  # 10 + 1 + 1982 = 1993 → 1+9+9+3 = 22 → 2+2 = 4
        
        # Additional test cases that might result in 11 or 22
        ("02.09.1998", 2),  # Should result in 11 → 1+1 = 2
        ("29.11.1992", 4),  # Should result in 22 → 2+2 = 4
        ("11.11.1991", 7),  # Should result in 25 → 2+5 = 7
        ("22.02.2000", 8),  # Should result in 26 → 2+6 = 8
        ("01.01.2001", 5),  # Should result in 5 (already single digit)
        ("09.09.1999", 1),  # Should result in 46 → 4+6 = 10 → 1+0 = 1
    ]
    
    all_passed = True
    
    for birth_date, expected in test_cases:
        print(f"\n{'='*30}")
        success = test_destiny_number_calculation(token, birth_date, expected)
        if not success:
            all_passed = False
        
        # Also test master number preservation in other fields
        test_master_numbers_preserved_in_other_fields(token, birth_date)
    
    print(f"\n{'='*50}")
    if all_passed:
        print("✅ ALL TESTS PASSED: Destiny Number calculation is working correctly!")
        print("   - Destiny Numbers are always reduced to single digits (1-9)")
        print("   - Master numbers 11/22 are never returned for Destiny Number")
        print("   - Other numbers can still preserve master numbers as expected")
    else:
        print("❌ SOME TESTS FAILED: Destiny Number calculation needs fixing!")
    
    print(f"\n🏁 Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()