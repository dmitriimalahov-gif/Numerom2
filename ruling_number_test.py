#!/usr/bin/env python3
"""
Focused test for Ruling Number (ПЧ) calculation fix
Testing the corrected implementation that sums ALL digits from date, month, year
and preserves master numbers 11 and 22.
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://numerology-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class RulingNumberTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        
    def register_test_user(self):
        """Login as super admin for unlimited testing"""
        login_data = {
            "email": "dmitrii.malahov@gmail.com",
            "password": "756bvy67H"
        }
        
        print(f"🔄 Logging in as super admin for testing")
        response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data['access_token']
            self.user_id = data['user']['id']
            self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
            print(f"✅ Super admin logged in successfully. User ID: {self.user_id}")
            print(f"   Credits: {data['user']['credits_remaining']}")
            print(f"   Premium: {data['user']['is_premium']}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def test_ruling_number_calculation(self, birth_date, expected_ruling_number, description):
        """Test ruling number calculation for a specific birth date"""
        print(f"\n🧮 Testing: {description}")
        print(f"   Birth date: {birth_date}")
        print(f"   Expected ruling number: {expected_ruling_number}")
        
        # Calculate digits manually for verification
        digits = [int(d) for d in birth_date.replace('.', '')]
        digit_sum = sum(digits)
        print(f"   Manual calculation: {' + '.join(map(str, digits))} = {digit_sum}")
        
        # If sum is not 11 or 22, reduce to single digit
        if digit_sum not in [11, 22]:
            while digit_sum > 9:
                new_digits = [int(d) for d in str(digit_sum)]
                digit_sum = sum(new_digits)
                print(f"   Reducing: {' + '.join(map(str, new_digits))} = {digit_sum}")
        
        response = self.session.post(f"{API_BASE}/numerology/personal-numbers", 
                                   params={"birth_date": birth_date})
        
        if response.status_code == 200:
            data = response.json()
            actual_ruling_number = data.get('ruling_number')
            helping_mind_number = data.get('helping_mind_number')
            
            print(f"   API Response:")
            print(f"     Ruling number (ПЧ): {actual_ruling_number}")
            print(f"     Helping mind number (ЧУ*): {helping_mind_number}")
            
            # Verify ruling number is correct
            if actual_ruling_number == expected_ruling_number:
                print(f"   ✅ PASS: Ruling number is correct ({actual_ruling_number})")
            else:
                print(f"   ❌ FAIL: Expected {expected_ruling_number}, got {actual_ruling_number}")
                return False
            
            # Verify helping mind number is different (day + month only)
            day, month, year = birth_date.split('.')
            expected_helping_mind = int(day) + int(month)
            # Use same reduction logic as the backend
            if expected_helping_mind in [11, 22, 33]:
                pass  # Keep master numbers
            else:
                while expected_helping_mind > 9:
                    expected_helping_mind = sum(int(d) for d in str(expected_helping_mind))
            
            if helping_mind_number == expected_helping_mind:
                print(f"   ✅ PASS: Helping mind number is correct ({helping_mind_number}) - different calculation from ruling number")
            else:
                print(f"   ❌ FAIL: Expected helping mind {expected_helping_mind}, got {helping_mind_number}")
                return False
            
            return True
        else:
            print(f"   ❌ API Error: {response.status_code} - {response.text}")
            return False
    
    def find_date_with_ruling_number_11(self):
        """Find a birth date that results in ruling number 11"""
        print(f"\n🔍 Searching for a date that gives ruling number 11...")
        
        # Try some dates that might give 11
        test_dates = [
            "02.09.1990",  # 2+0+0+9+1+9+9+0 = 30 -> 3+0 = 3 (no)
            "11.11.1111",  # 1+1+1+1+1+1+1+1 = 8 (no)
            "29.01.1990",  # 2+9+0+1+1+9+9+0 = 31 -> 3+1 = 4 (no)
            "19.01.1990",  # 1+9+0+1+1+9+9+0 = 30 -> 3+0 = 3 (no)
            "28.01.1990",  # 2+8+0+1+1+9+9+0 = 30 -> 3+0 = 3 (no)
            "01.01.1999",  # 0+1+0+1+1+9+9+9 = 30 -> 3+0 = 3 (no)
            "02.09.1999",  # 0+2+0+9+1+9+9+9 = 39 -> 3+9 = 12 -> 1+2 = 3 (no)
            "11.01.1999",  # 1+1+0+1+1+9+9+9 = 31 -> 3+1 = 4 (no)
            "20.09.1999",  # 2+0+0+9+1+9+9+9 = 39 -> 3+9 = 12 -> 1+2 = 3 (no)
            "29.09.1999",  # 2+9+0+9+1+9+9+9 = 48 -> 4+8 = 12 -> 1+2 = 3 (no)
            "02.09.2000",  # 0+2+0+9+2+0+0+0 = 13 -> 1+3 = 4 (no)
            "29.09.2000",  # 2+9+0+9+2+0+0+0 = 22 (master number, not 11)
            "11.09.2000",  # 1+1+0+9+2+0+0+0 = 13 -> 1+3 = 4 (no)
            "02.09.1991",  # 0+2+0+9+1+9+9+1 = 31 -> 3+1 = 4 (no)
            "11.09.1991",  # 1+1+0+9+1+9+9+1 = 31 -> 3+1 = 4 (no)
            "20.09.1991",  # 2+0+0+9+1+9+9+1 = 31 -> 3+1 = 4 (no)
            "29.09.1991",  # 2+9+0+9+1+9+9+1 = 40 -> 4+0 = 4 (no)
            "11.09.1992",  # 1+1+0+9+1+9+9+2 = 32 -> 3+2 = 5 (no)
            "20.09.1992",  # 2+0+0+9+1+9+9+2 = 32 -> 3+2 = 5 (no)
            "29.09.1992",  # 2+9+0+9+1+9+9+2 = 41 -> 4+1 = 5 (no)
            "11.09.1993",  # 1+1+0+9+1+9+9+3 = 33 (master number, not 11)
            "02.09.1993",  # 0+2+0+9+1+9+9+3 = 33 (master number, not 11)
            "20.09.1993",  # 2+0+0+9+1+9+9+3 = 33 (master number, not 11)
            "29.09.1993",  # 2+9+0+9+1+9+9+3 = 42 -> 4+2 = 6 (no)
            "11.09.1994",  # 1+1+0+9+1+9+9+4 = 34 -> 3+4 = 7 (no)
            "02.09.1994",  # 0+2+0+9+1+9+9+4 = 34 -> 3+4 = 7 (no)
            "20.09.1994",  # 2+0+0+9+1+9+9+4 = 34 -> 3+4 = 7 (no)
            "29.09.1994",  # 2+9+0+9+1+9+9+4 = 43 -> 4+3 = 7 (no)
            "11.09.1995",  # 1+1+0+9+1+9+9+5 = 35 -> 3+5 = 8 (no)
            "02.09.1995",  # 0+2+0+9+1+9+9+5 = 35 -> 3+5 = 8 (no)
            "20.09.1995",  # 2+0+0+9+1+9+9+5 = 35 -> 3+5 = 8 (no)
            "29.09.1995",  # 2+9+0+9+1+9+9+5 = 44 -> 4+4 = 8 (no)
            "11.09.1996",  # 1+1+0+9+1+9+9+6 = 36 -> 3+6 = 9 (no)
            "02.09.1996",  # 0+2+0+9+1+9+9+6 = 36 -> 3+6 = 9 (no)
            "20.09.1996",  # 2+0+0+9+1+9+9+6 = 36 -> 3+6 = 9 (no)
            "29.09.1996",  # 2+9+0+9+1+9+9+6 = 45 -> 4+5 = 9 (no)
            "11.09.1997",  # 1+1+0+9+1+9+9+7 = 37 -> 3+7 = 10 -> 1+0 = 1 (no)
            "02.09.1997",  # 0+2+0+9+1+9+9+7 = 37 -> 3+7 = 10 -> 1+0 = 1 (no)
            "20.09.1997",  # 2+0+0+9+1+9+9+7 = 37 -> 3+7 = 10 -> 1+0 = 1 (no)
            "29.09.1997",  # 2+9+0+9+1+9+9+7 = 46 -> 4+6 = 10 -> 1+0 = 1 (no)
            "11.09.1998",  # 1+1+0+9+1+9+9+8 = 38 -> 3+8 = 11 (YES!)
        ]
        
        for date in test_dates:
            digits = [int(d) for d in date.replace('.', '')]
            digit_sum = sum(digits)
            
            if digit_sum == 11:
                print(f"   ✅ Found date with ruling number 11: {date}")
                print(f"      Digits: {' + '.join(map(str, digits))} = {digit_sum}")
                return date
            elif digit_sum == 22:
                print(f"   📝 Found date with ruling number 22: {date}")
                print(f"      Digits: {' + '.join(map(str, digits))} = {digit_sum}")
            else:
                # Reduce to single digit
                reduced = digit_sum
                while reduced > 9:
                    reduced = sum(int(d) for d in str(reduced))
                if reduced == 11:  # This shouldn't happen, but just in case
                    print(f"   ✅ Found date with ruling number 11 (after reduction): {date}")
                    return date
        
        # If we didn't find one, let's construct one mathematically
        # We need digits that sum to 11
        # Let's try: 02.09.1998 = 0+2+0+9+1+9+9+8 = 38 -> 3+8 = 11
        constructed_date = "02.09.1998"
        digits = [int(d) for d in constructed_date.replace('.', '')]
        digit_sum = sum(digits)
        if digit_sum != 11:
            digit_sum = sum(int(d) for d in str(digit_sum))
        
        if digit_sum == 11:
            print(f"   ✅ Constructed date with ruling number 11: {constructed_date}")
            return constructed_date
        
        print(f"   ⚠️  Could not find a date that gives ruling number 11")
        return None
    
    def run_all_tests(self):
        """Run all ruling number tests"""
        print("=" * 60)
        print("🧮 RULING NUMBER (ПЧ) CALCULATION TESTS")
        print("=" * 60)
        
        if not self.register_test_user():
            return False
        
        all_passed = True
        
        # Test case 1: 10.01.1982 should give 22 (not reduced to 4)
        if not self.test_ruling_number_calculation(
            "10.01.1982", 22, 
            "Master number 22 preservation (1+0+0+1+1+9+8+2 = 22)"
        ):
            all_passed = False
        
        # Test case 2: 15.03.1990 should give 1 (28 -> 10 -> 1)
        if not self.test_ruling_number_calculation(
            "15.03.1990", 1,
            "Regular reduction (1+5+0+3+1+9+9+0 = 28 → 2+8 = 10 → 1+0 = 1)"
        ):
            all_passed = False
        
        # Test case 3: Find and test a date that gives 11
        date_with_11 = self.find_date_with_ruling_number_11()
        if date_with_11:
            if not self.test_ruling_number_calculation(
                date_with_11, 11,
                "Master number 11 preservation"
            ):
                all_passed = False
        else:
            print("   ⚠️  Skipping master number 11 test - no suitable date found")
        
        # Additional test cases to verify the algorithm
        test_cases = [
            ("01.01.2000", 4, "Simple case (0+1+0+1+2+0+0+0 = 4)"),
            ("31.12.1999", 8, "End of millennium (3+1+1+2+1+9+9+9 = 35 → 3+5 = 8)"),
            ("29.02.2000", 6, "Leap year (2+9+0+2+2+0+0+0 = 15 → 1+5 = 6)"),
        ]
        
        for birth_date, expected, description in test_cases:
            if not self.test_ruling_number_calculation(birth_date, expected, description):
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL RULING NUMBER TESTS PASSED!")
            print("✅ Ruling number correctly sums ALL digits from birth date")
            print("✅ Master numbers 11 and 22 are preserved (not reduced)")
            print("✅ Helping mind number is different (day + month only)")
        else:
            print("❌ SOME TESTS FAILED!")
            print("   Please check the ruling number calculation implementation")
        print("=" * 60)
        
        return all_passed

if __name__ == "__main__":
    tester = RulingNumberTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)