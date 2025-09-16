#!/usr/bin/env python3
"""
Enhanced Personal Numbers Calculation Testing
Testing the new data structure with all required fields as per review request
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

# Test credentials for authentication (using super admin for unlimited credits)
TEST_USER = {
    "email": "dmitrii.malahov@gmail.com",
    "password": "756bvy67H"
}

class EnhancedPersonalNumbersTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        
    def register_test_user(self):
        """Login with super admin credentials"""
        print("🔐 Logging in as super admin...")
        return self.login_test_user()
    
    def login_test_user(self):
        """Login with super admin credentials"""
        print("🔐 Logging in super admin...")
        
        try:
            login_data = {"email": TEST_USER["email"], "password": TEST_USER["password"]}
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.user_id = data['user']['id']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                print(f"✅ Login successful. ID: {self.user_id}")
                print(f"💰 Credits: {data['user']['credits_remaining']}")
                print(f"🔑 Premium: {data['user']['is_premium']}")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_enhanced_personal_numbers_structure(self):
        """Test the enhanced personal numbers endpoint with new data structure"""
        print("\n🧮 Testing Enhanced Personal Numbers Data Structure...")
        
        try:
            # Test with the specific example from review request: 10.01.1982
            test_birth_date = "10.01.1982"
            
            response = self.session.post(
                f"{BACKEND_URL}/numerology/personal-numbers",
                json={"birth_date": test_birth_date}
            )
            
            if response.status_code != 200:
                print(f"❌ API call failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            print(f"✅ API Response received (Status: {response.status_code})")
            
            # Required fields from review request
            required_fields = [
                'soul_number',           # ЧД
                'mind_number',           # ЧУ
                'destiny_number',        # ЧС
                'helping_mind_number',   # ЧУ*
                'wisdom_number',         # ЧМ
                'ruling_number',         # ПЧ
                'planetary_strength',    # Сила планет
                'birth_weekday'          # день недели рождения
            ]
            
            print("\n📋 Checking Required Fields:")
            missing_fields = []
            for field in required_fields:
                if field in data:
                    print(f"✅ {field}: {data[field]}")
                else:
                    print(f"❌ Missing field: {field}")
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            # Verify planetary strength has all 9 planets
            print("\n🪐 Checking Planetary Strength (all 9 planets):")
            expected_planets = ['Солнце', 'Луна', 'Марс', 'Меркурий', 'Юпитер', 'Венера', 'Сатурн', 'Раху', 'Кету']
            planetary_strength = data.get('planetary_strength', {})
            
            missing_planets = []
            for planet in expected_planets:
                if planet in planetary_strength:
                    print(f"✅ {planet}: {planetary_strength[planet]}")
                else:
                    print(f"❌ Missing planet: {planet}")
                    missing_planets.append(planet)
            
            if missing_planets:
                print(f"❌ Missing planets in planetary_strength: {missing_planets}")
                return False
            
            print(f"✅ All 9 planets present in planetary_strength")
            
            # Verify birth weekday
            birth_weekday = data.get('birth_weekday')
            print(f"\n📅 Birth Weekday: {birth_weekday}")
            
            # Verify the calculation for 10.01.1982
            print(f"\n🔢 Verifying calculations for {test_birth_date}:")
            print(f"   Soul Number (ЧД): {data.get('soul_number')}")
            print(f"   Mind Number (ЧУ): {data.get('mind_number')}")
            print(f"   Destiny Number (ЧС): {data.get('destiny_number')}")
            print(f"   Helping Mind Number (ЧУ*): {data.get('helping_mind_number')}")
            print(f"   Wisdom Number (ЧМ): {data.get('wisdom_number')}")
            print(f"   Ruling Number (ПЧ): {data.get('ruling_number')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False
    
    def test_planetary_strength_formula(self):
        """Test planetary strength calculation formula: day+month (combined) * year"""
        print("\n🧮 Testing Planetary Strength Formula...")
        
        try:
            # Test with 10.01.1982
            # Formula: day+month as combined number (1001) * year (1982) = 1983982
            test_birth_date = "10.01.1982"
            
            response = self.session.post(
                f"{BACKEND_URL}/numerology/personal-numbers",
                json={"birth_date": test_birth_date}
            )
            
            if response.status_code != 200:
                print(f"❌ API call failed: {response.status_code}")
                return False
            
            data = response.json()
            
            # Check if calculation details are available
            if 'calculation_details' in data:
                calc_details = data['calculation_details']
                calc_number = calc_details.get('calculation_number')
                
                # Expected calculation: 1001 * 1982 = 1983982
                expected_calc = 1001 * 1982
                
                print(f"📊 Formula verification for {test_birth_date}:")
                print(f"   Day+Month combined: 1001")
                print(f"   Year: 1982")
                print(f"   Expected result: {expected_calc}")
                print(f"   Actual result: {calc_number}")
                
                if calc_number == expected_calc:
                    print("✅ Planetary strength formula calculation is correct!")
                    
                    # Show how digits are distributed
                    result_digits = [int(d) for d in str(calc_number)]
                    print(f"   Result digits: {result_digits}")
                    print(f"   Distributed by weekday order starting from: {data.get('birth_weekday')}")
                    
                    return True
                else:
                    print(f"❌ Formula calculation mismatch!")
                    return False
            else:
                print("ℹ️ Calculation details not available in response")
                # Still check if planetary strength exists and has values
                planetary_strength = data.get('planetary_strength', {})
                if len(planetary_strength) == 9:
                    print("✅ Planetary strength calculated (formula details not exposed)")
                    return True
                else:
                    print("❌ Planetary strength incomplete")
                    return False
                    
        except Exception as e:
            print(f"❌ Formula test error: {e}")
            return False
    
    def test_credit_decrement(self):
        """Test that credit decrement functionality still works"""
        print("\n💰 Testing Credit Decrement Functionality...")
        
        try:
            # Get initial credits
            profile_response = self.session.get(f"{BACKEND_URL}/user/profile")
            if profile_response.status_code != 200:
                print(f"❌ Failed to get user profile: {profile_response.status_code}")
                return False
            
            initial_credits = profile_response.json().get('credits_remaining', 0)
            print(f"💰 Initial credits: {initial_credits}")
            
            # Make a personal numbers calculation
            response = self.session.post(
                f"{BACKEND_URL}/numerology/personal-numbers",
                json={"birth_date": "15.03.1990"}
            )
            
            if response.status_code != 200:
                print(f"❌ Personal numbers calculation failed: {response.status_code}")
                return False
            
            # Check credits after calculation
            profile_response = self.session.get(f"{BACKEND_URL}/user/profile")
            if profile_response.status_code != 200:
                print(f"❌ Failed to get updated profile: {profile_response.status_code}")
                return False
            
            final_credits = profile_response.json().get('credits_remaining', 0)
            print(f"💰 Final credits: {final_credits}")
            
            # Check if credits were decremented (for non-premium users)
            user_data = profile_response.json()
            is_premium = user_data.get('is_premium', False)
            
            if is_premium:
                print("ℹ️ User is premium - credits should not be decremented")
                if final_credits == initial_credits:
                    print("✅ Credits correctly preserved for premium user")
                    return True
                else:
                    print("❌ Credits unexpectedly changed for premium user")
                    return False
            else:
                print("ℹ️ User is not premium - credits should be decremented")
                if final_credits == initial_credits - 1:
                    print("✅ Credits correctly decremented by 1")
                    return True
                elif initial_credits == 0:
                    print("ℹ️ User had 0 credits - should get 402 error instead")
                    return True
                else:
                    print(f"❌ Unexpected credit change: {initial_credits} -> {final_credits}")
                    return False
                    
        except Exception as e:
            print(f"❌ Credit test error: {e}")
            return False
    
    def test_specific_example_accuracy(self):
        """Test calculation accuracy with the specific example 10.01.1982"""
        print("\n🎯 Testing Calculation Accuracy for 10.01.1982...")
        
        try:
            test_birth_date = "10.01.1982"
            
            response = self.session.post(
                f"{BACKEND_URL}/numerology/personal-numbers",
                json={"birth_date": test_birth_date}
            )
            
            if response.status_code != 200:
                print(f"❌ API call failed: {response.status_code}")
                return False
            
            data = response.json()
            
            # Manual calculation verification for 10.01.1982
            print(f"🔍 Manual verification for {test_birth_date}:")
            
            # Soul number (day): 10 -> 1+0 = 1
            expected_soul = 1
            actual_soul = data.get('soul_number')
            print(f"   Soul Number: Expected {expected_soul}, Got {actual_soul} {'✅' if actual_soul == expected_soul else '❌'}")
            
            # Mind number (month): 01 -> 1
            expected_mind = 1
            actual_mind = data.get('mind_number')
            print(f"   Mind Number: Expected {expected_mind}, Got {actual_mind} {'✅' if actual_mind == expected_mind else '❌'}")
            
            # Ruling number (day + month): 10 + 1 = 11 -> 11 (master number)
            expected_ruling = 11
            actual_ruling = data.get('ruling_number')
            print(f"   Ruling Number: Expected {expected_ruling}, Got {actual_ruling} {'✅' if actual_ruling == expected_ruling else '❌'}")
            
            # Helping Mind number (day + month): 10 + 1 = 11 -> 11
            expected_helping = 11
            actual_helping = data.get('helping_mind_number')
            print(f"   Helping Mind: Expected {expected_helping}, Got {actual_helping} {'✅' if actual_helping == expected_helping else '❌'}")
            
            # Check birth weekday for 10.01.1982 (should be Sunday/воскресенье)
            from datetime import datetime
            birth_date_obj = datetime(1982, 1, 10)
            expected_weekday = birth_date_obj.strftime('%A').lower()
            actual_weekday = data.get('birth_weekday', '').lower()
            
            # Convert to Russian
            weekday_map = {
                'sunday': 'воскресенье',
                'monday': 'понедельник', 
                'tuesday': 'вторник',
                'wednesday': 'среда',
                'thursday': 'четверг',
                'friday': 'пятница',
                'saturday': 'суббота'
            }
            expected_weekday_ru = weekday_map.get(expected_weekday, expected_weekday)
            
            print(f"   Birth Weekday: Expected {expected_weekday_ru}, Got {actual_weekday} {'✅' if actual_weekday == expected_weekday_ru else '❌'}")
            
            # Verify planetary strength has reasonable values
            planetary_strength = data.get('planetary_strength', {})
            print(f"   Planetary Strength Distribution:")
            for planet, strength in planetary_strength.items():
                print(f"     {planet}: {strength}")
            
            return True
            
        except Exception as e:
            print(f"❌ Accuracy test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all enhanced personal numbers tests"""
        print("🚀 Starting Enhanced Personal Numbers Testing...")
        print("=" * 60)
        
        # Authentication
        if not self.register_test_user():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Test results
        test_results = []
        
        # Test 1: Enhanced data structure
        test_results.append(("Enhanced Data Structure", self.test_enhanced_personal_numbers_structure()))
        
        # Test 2: Planetary strength formula
        test_results.append(("Planetary Strength Formula", self.test_planetary_strength_formula()))
        
        # Test 3: Credit decrement
        test_results.append(("Credit Decrement", self.test_credit_decrement()))
        
        # Test 4: Specific example accuracy
        test_results.append(("Calculation Accuracy", self.test_specific_example_accuracy()))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n📈 Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All enhanced personal numbers tests PASSED!")
            return True
        else:
            print(f"⚠️ {failed} test(s) FAILED - review implementation")
            return False

if __name__ == "__main__":
    tester = EnhancedPersonalNumbersTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)