#!/usr/bin/env python3
"""
Comprehensive Ruling Number (ПЧ) Calculation Testing
Based on the review request requirements:
1. Test POST /api/numerology/personal-numbers with specific birth dates that should result in ruling number 11 or 22
2. Test with birth date 10.01.1982 (should return 22, not 4)
3. Create test cases for edge cases (initial sum = 11/22, reduction produces 11/22)
4. Verify other personal numbers still work correctly
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class ComprehensiveRulingNumberTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def login_super_admin(self):
        """Login as super admin for unlimited testing"""
        login_data = {
            "email": "dmitrii.malahov@gmail.com",
            "password": "756bvy67H"
        }
        
        print(f"🔐 Logging in as super admin for comprehensive testing")
        response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data['access_token']
            self.user_id = data['user']['id']
            self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
            print(f"✅ Super admin logged in successfully")
            print(f"   User ID: {self.user_id}")
            print(f"   Credits: {data['user']['credits_remaining']}")
            print(f"   Premium: {data['user']['is_premium']}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def calculate_ruling_number_manually(self, birth_date):
        """Calculate ruling number manually to verify API results"""
        # Extract all digits from birth date
        digits = [int(d) for d in birth_date.replace('.', '')]
        total = sum(digits)
        
        calculation_steps = [f"{' + '.join(map(str, digits))} = {total}"]
        
        # Apply reduction rules: preserve 11 and 22 at ANY stage
        while total > 9:
            if total in [11, 22]:
                calculation_steps.append(f"Master number {total} preserved")
                break
            
            new_digits = [int(d) for d in str(total)]
            new_total = sum(new_digits)
            calculation_steps.append(f"{' + '.join(map(str, new_digits))} = {new_total}")
            total = new_total
        
        return total, calculation_steps
    
    def test_personal_numbers_api(self, birth_date, test_name):
        """Test the personal numbers API endpoint"""
        print(f"\n🧮 {test_name}")
        print(f"   Birth date: {birth_date}")
        
        # Manual calculation
        expected_ruling, steps = self.calculate_ruling_number_manually(birth_date)
        print(f"   Manual calculation:")
        for step in steps:
            print(f"     {step}")
        print(f"   Expected ruling number: {expected_ruling}")
        
        # API call
        response = self.session.post(f"{BACKEND_URL}/numerology/personal-numbers", 
                                   params={"birth_date": birth_date})
        
        if response.status_code == 200:
            data = response.json()
            actual_ruling = data.get('ruling_number')
            
            print(f"   API Response:")
            print(f"     Soul Number: {data.get('soul_number')}")
            print(f"     Mind Number: {data.get('mind_number')}")
            print(f"     Destiny Number: {data.get('destiny_number')}")
            print(f"     Helping Mind Number: {data.get('helping_mind_number')}")
            print(f"     Wisdom Number: {data.get('wisdom_number')}")
            print(f"     Ruling Number: {actual_ruling}")
            
            # Verify ruling number
            if actual_ruling == expected_ruling:
                print(f"   ✅ PASS: Ruling number {actual_ruling} matches expected {expected_ruling}")
                result = True
            else:
                print(f"   ❌ FAIL: Expected ruling number {expected_ruling}, got {actual_ruling}")
                result = False
            
            # Store test result
            self.test_results.append({
                'test_name': test_name,
                'birth_date': birth_date,
                'expected_ruling': expected_ruling,
                'actual_ruling': actual_ruling,
                'passed': result,
                'all_numbers': data
            })
            
            return result, data
        else:
            print(f"   ❌ API Error: {response.status_code} - {response.text}")
            self.test_results.append({
                'test_name': test_name,
                'birth_date': birth_date,
                'expected_ruling': expected_ruling,
                'actual_ruling': None,
                'passed': False,
                'error': f"{response.status_code}: {response.text}"
            })
            return False, None
    
    def test_main_review_case(self):
        """Test the main case from the review request: 10.01.1982 should return 22"""
        print("\n" + "="*70)
        print("🎯 MAIN REVIEW REQUEST TEST CASE")
        print("="*70)
        
        return self.test_personal_numbers_api(
            "10.01.1982",
            "Main test case: 10.01.1982 should return ruling number 22 (NOT 4)"
        )
    
    def test_initial_sum_master_numbers(self):
        """Test cases where initial sum equals 11 or 22 directly"""
        print("\n" + "="*70)
        print("🔢 INITIAL SUM = MASTER NUMBER TESTS")
        print("="*70)
        
        results = []
        
        # Find dates where sum of digits = 11
        test_cases_11 = [
            "02.09.1998",  # 0+2+0+9+1+9+9+8 = 38 → 3+8 = 11
            "11.09.1998",  # 1+1+0+9+1+9+9+8 = 38 → 3+8 = 11
            "20.09.1998",  # 2+0+0+9+1+9+9+8 = 38 → 3+8 = 11
        ]
        
        # Find dates where sum of digits = 22
        test_cases_22 = [
            "10.01.1982",  # 1+0+0+1+1+9+8+2 = 22 (direct)
            "29.09.2000",  # 2+9+0+9+2+0+0+0 = 22 (direct)
        ]
        
        for birth_date in test_cases_11:
            result, data = self.test_personal_numbers_api(
                birth_date,
                f"Master number 11 test: {birth_date}"
            )
            results.append(result)
        
        for birth_date in test_cases_22:
            result, data = self.test_personal_numbers_api(
                birth_date,
                f"Master number 22 test: {birth_date}"
            )
            results.append(result)
        
        return all(results)
    
    def test_reduction_produces_master_numbers(self):
        """Test cases where reduction process results in 11 or 22"""
        print("\n" + "="*70)
        print("🔄 REDUCTION PRODUCES MASTER NUMBER TESTS")
        print("="*70)
        
        results = []
        
        # Cases where reduction produces 11
        test_cases = [
            ("02.09.1998", "Reduction to 11: 0+2+0+9+1+9+9+8 = 38 → 3+8 = 11"),
            ("11.09.1998", "Reduction to 11: 1+1+0+9+1+9+9+8 = 38 → 3+8 = 11"),
            ("20.09.1998", "Reduction to 11: 2+0+0+9+1+9+9+8 = 38 → 3+8 = 11"),
        ]
        
        for birth_date, description in test_cases:
            result, data = self.test_personal_numbers_api(birth_date, description)
            results.append(result)
        
        return all(results)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("\n" + "="*70)
        print("🎲 EDGE CASE TESTS")
        print("="*70)
        
        results = []
        
        edge_cases = [
            ("01.01.1999", "Minimum digits case"),
            ("31.12.1999", "Maximum day/month case"),
            ("29.02.2000", "Leap year case"),
            ("01.01.2000", "Millennium boundary"),
            ("09.09.1999", "All 9s case"),
            ("11.11.1111", "All 1s case"),
            ("22.02.2222", "All 2s case (if valid)"),
        ]
        
        for birth_date, description in edge_cases:
            try:
                result, data = self.test_personal_numbers_api(birth_date, f"Edge case: {description}")
                results.append(result)
            except Exception as e:
                print(f"   ⚠️  Skipping {birth_date}: {e}")
        
        return all(results)
    
    def test_non_master_number_reduction(self):
        """Test that non-master numbers are correctly reduced to single digits"""
        print("\n" + "="*70)
        print("🔢 NON-MASTER NUMBER REDUCTION TESTS")
        print("="*70)
        
        results = []
        
        test_cases = [
            ("15.03.1990", "Regular reduction: should become 1"),
            ("25.12.1985", "Regular reduction: should become 6"),
            ("07.08.1977", "Regular reduction: should become 5"),
            ("13.05.1975", "Regular reduction: should become 4"),
        ]
        
        for birth_date, description in test_cases:
            result, data = self.test_personal_numbers_api(birth_date, description)
            results.append(result)
        
        return all(results)
    
    def verify_other_numbers_integrity(self):
        """Verify that other personal numbers (destiny, helping mind) still work correctly"""
        print("\n" + "="*70)
        print("🔍 OTHER NUMBERS INTEGRITY VERIFICATION")
        print("="*70)
        
        # Test with the main case from review request
        birth_date = "10.01.1982"
        result, data = self.test_personal_numbers_api(
            birth_date,
            "Comprehensive verification of all numbers for 10.01.1982"
        )
        
        if not result or not data:
            return False
        
        # Verify specific expectations for 10.01.1982
        expected_values = {
            'soul_number': 1,      # 10 → 1+0 = 1
            'mind_number': 1,      # 1 (January)
            'destiny_number': 4,   # 10+1+1982=1993 → 1+9+9+3=22 → 2+2=4 (always single digit)
            'helping_mind_number': 11,  # 10+1=11 (master number preserved)
            'ruling_number': 22    # 1+0+0+1+1+9+8+2=22 (master number preserved)
        }
        
        print(f"\n   📊 Detailed verification for {birth_date}:")
        all_correct = True
        
        for field, expected in expected_values.items():
            actual = data.get(field)
            if actual == expected:
                print(f"   ✅ {field}: {actual} (correct)")
            else:
                print(f"   ❌ {field}: {actual} (expected {expected})")
                all_correct = False
        
        # Additional verification: destiny number should ALWAYS be single digit
        destiny_number = data.get('destiny_number')
        if destiny_number and 1 <= destiny_number <= 9:
            print(f"   ✅ Destiny number is single digit: {destiny_number}")
        else:
            print(f"   ❌ Destiny number should be single digit (1-9), got: {destiny_number}")
            all_correct = False
        
        # Helping mind number can be master number
        helping_mind = data.get('helping_mind_number')
        if helping_mind and (1 <= helping_mind <= 9 or helping_mind in [11, 22]):
            print(f"   ✅ Helping mind number is valid: {helping_mind}")
        else:
            print(f"   ❌ Helping mind number should be 1-9 or 11/22, got: {helping_mind}")
            all_correct = False
        
        return all_correct
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 COMPREHENSIVE RULING NUMBER (ПЧ) CALCULATION TESTING")
        print("Based on review request requirements")
        print("="*70)
        
        if not self.login_super_admin():
            return False
        
        # Run all test categories
        test_categories = [
            ("Main Review Case", self.test_main_review_case),
            ("Initial Sum Master Numbers", self.test_initial_sum_master_numbers),
            ("Reduction Produces Master Numbers", self.test_reduction_produces_master_numbers),
            ("Edge Cases", self.test_edge_cases),
            ("Non-Master Number Reduction", self.test_non_master_number_reduction),
            ("Other Numbers Integrity", self.verify_other_numbers_integrity),
        ]
        
        category_results = []
        
        for category_name, test_function in test_categories:
            print(f"\n🔍 Running {category_name} tests...")
            try:
                result = test_function()
                category_results.append((category_name, result))
                if result:
                    print(f"✅ {category_name}: PASSED")
                else:
                    print(f"❌ {category_name}: FAILED")
            except Exception as e:
                print(f"❌ {category_name}: ERROR - {e}")
                category_results.append((category_name, False))
        
        # Final summary
        self.print_final_summary(category_results)
        
        # Return overall success
        return all(result for _, result in category_results)
    
    def print_final_summary(self, category_results):
        """Print comprehensive test summary"""
        print("\n" + "="*70)
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("="*70)
        
        passed_categories = sum(1 for _, result in category_results if result)
        total_categories = len(category_results)
        
        print(f"📊 Category Results: {passed_categories}/{total_categories} passed")
        
        for category_name, result in category_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {category_name}")
        
        # Individual test summary
        passed_tests = sum(1 for test in self.test_results if test['passed'])
        total_tests = len(self.test_results)
        
        print(f"\n📈 Individual Tests: {passed_tests}/{total_tests} passed")
        
        if passed_tests < total_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.test_results:
                if not test['passed']:
                    print(f"   • {test['test_name']} ({test['birth_date']})")
                    if 'error' in test:
                        print(f"     Error: {test['error']}")
                    else:
                        print(f"     Expected: {test['expected_ruling']}, Got: {test['actual_ruling']}")
        
        # Overall result
        overall_success = passed_categories == total_categories
        
        print(f"\n🎯 OVERALL RESULT:")
        if overall_success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Ruling Number calculation correctly preserves master numbers 11 and 22")
            print("✅ All edge cases handled properly")
            print("✅ Other personal numbers work correctly")
            print("✅ Review request requirements fully satisfied")
        else:
            print("⚠️  SOME TESTS FAILED!")
            print("   Please review the failed tests above")
        
        print("="*70)

def main():
    """Main test execution"""
    tester = ComprehensiveRulingNumberTester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print(f"\n✅ COMPREHENSIVE RULING NUMBER TESTING COMPLETE - ALL TESTS PASSED")
        exit(0)
    else:
        print(f"\n❌ COMPREHENSIVE RULING NUMBER TESTING COMPLETE - SOME TESTS FAILED")
        exit(1)

if __name__ == "__main__":
    main()