#!/usr/bin/env python3
"""
Direct test of the planetary strength calculation function
Testing the review request requirements for birth date 10.01.1982
"""

import sys
import os
sys.path.append('/app/backend')

from numerology import calculate_personal_numbers, calculate_planetary_strength, parse_birth_date
from datetime import datetime

def test_planetary_strength_direct():
    """Test planetary strength calculation directly"""
    print("🚀 Testing Planetary Strength Calculation (Direct Function Test)")
    print("=" * 70)
    print("Testing with birth date: 10.01.1982")
    print("=" * 70)
    
    test_results = []
    
    def log_result(test_name, success, message="", details=None):
        result = {"test": test_name, "success": success, "message": message, "details": details}
        test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    try:
        # Test the specific birth date from review request
        birth_date = "10.01.1982"
        day, month, year = parse_birth_date(birth_date)
        
        # Test 1: Calculate personal numbers
        personal_numbers = calculate_personal_numbers(birth_date)
        
        # Test 2: Check that only 7 planets are present (no Rahu/Ketu)
        planetary_strength = personal_numbers.get("planetary_strength", {})
        expected_planets = ['Солнце', 'Луна', 'Марс', 'Меркурий', 'Юпитер', 'Венера', 'Сатурн']
        forbidden_planets = ['Раху', 'Кету']
        
        # Verify all expected planets are present
        missing_planets = [planet for planet in expected_planets if planet not in planetary_strength]
        if missing_planets:
            log_result("7 Planets Test", False, f"Missing planets: {missing_planets}", planetary_strength)
        else:
            # Verify forbidden planets are not present
            forbidden_found = [planet for planet in forbidden_planets if planet in planetary_strength]
            if forbidden_found:
                log_result("7 Planets Test", False, f"Forbidden planets found: {forbidden_found}", planetary_strength)
            else:
                # Verify exactly 7 planets
                if len(planetary_strength) != 7:
                    log_result("7 Planets Test", False, f"Expected 7 planets, got {len(planetary_strength)}", planetary_strength)
                else:
                    log_result("7 Planets Test", True, f"Exactly 7 planets present: {list(planetary_strength.keys())}")
        
        # Test 3: Check calculation formula (day+month combined * year)
        planetary_data = calculate_planetary_strength(day, month, year)
        expected_calculation = 1001 * 1982  # 10.01 -> 1001, year 1982
        actual_calculation = planetary_data.get("calculation_number", 0)
        
        if actual_calculation == expected_calculation:
            log_result("Calculation Formula Test", True, 
                      f"Formula correct: 1001 * 1982 = {actual_calculation}")
        else:
            log_result("Calculation Formula Test", False, 
                      f"Formula incorrect: expected {expected_calculation}, got {actual_calculation}", planetary_data)
        
        # Test 4: Check weekday mapping and birth weekday
        birth_weekday = personal_numbers.get("birth_weekday", "")
        if birth_weekday:
            log_result("Birth Weekday Test", True, f"Birth weekday present: {birth_weekday}")
            
            # Check if 10.01.1982 was indeed a Sunday
            birth_date_obj = datetime(1982, 1, 10)
            actual_weekday = birth_date_obj.weekday()  # 0=Monday, 6=Sunday
            if actual_weekday == 6:  # Sunday
                if "воскресенье" in birth_weekday.lower():
                    log_result("Sunday Verification Test", True, "Birth date correctly identified as Sunday")
                else:
                    log_result("Sunday Verification Test", False, f"Expected Sunday, got {birth_weekday}")
            else:
                log_result("Sunday Verification Test", False, f"Date calculation error: {birth_date_obj.strftime('%A')} != Sunday")
        else:
            log_result("Birth Weekday Test", False, "Birth weekday missing", personal_numbers)
        
        # Test 5: Check weekday mapping structure
        weekday_map = planetary_data.get("weekday_map", {})
        if weekday_map:
            # Should have 7 entries mapping planets to weekday abbreviations
            if len(weekday_map) == 7:
                # Check if Солнце maps to ВС (Sunday)
                if weekday_map.get("Солнце") == "ВС":
                    log_result("Weekday Mapping Test", True, f"Weekday mapping correct: Солнце = ВС")
                else:
                    log_result("Weekday Mapping Test", False, f"Солнце should map to ВС, got {weekday_map.get('Солнце')}", weekday_map)
            else:
                log_result("Weekday Mapping Test", False, f"Expected 7 weekday mappings, got {len(weekday_map)}", weekday_map)
        else:
            log_result("Weekday Mapping Test", False, "Weekday map missing", planetary_data)
        
        # Test 6: Check planetary strength values distribution
        # For 10.01.1982: 1001 * 1982 = 1983982
        # Digits: [1, 9, 8, 3, 9, 8, 2]
        # Starting from Sunday (Солнце), these should be distributed among the 7 planets
        expected_digits = [1, 9, 8, 3, 9, 8, 2]
        actual_values = []
        
        # Get values in the order they should appear (starting from Солнце for Sunday birth)
        planet_order = ['Солнце', 'Луна', 'Марс', 'Меркурий', 'Юпитер', 'Венера', 'Сатурн']
        for planet in planet_order:
            if planet in planetary_strength:
                actual_values.append(planetary_strength[planet])
        
        if actual_values == expected_digits:
            log_result("Planetary Values Distribution Test", True, 
                      f"Values correctly distributed: {actual_values}")
        else:
            log_result("Planetary Values Distribution Test", False, 
                      f"Expected {expected_digits}, got {actual_values}", 
                      {"planetary_strength": planetary_strength, "calculation": actual_calculation})
        
        # Test 7: Check response structure completeness
        required_fields = ["soul_number", "mind_number", "destiny_number", "helping_mind_number", 
                          "wisdom_number", "ruling_number", "planetary_strength", "birth_weekday"]
        missing_fields = [field for field in required_fields if field not in personal_numbers]
        
        if missing_fields:
            log_result("Response Structure Test", False, f"Missing fields: {missing_fields}", list(personal_numbers.keys()))
        else:
            log_result("Response Structure Test", True, "All required fields present")
        
        # Print detailed results
        print("\n" + "=" * 70)
        print("📊 DETAILED RESULTS")
        print("=" * 70)
        print(f"Birth Date: {birth_date}")
        print(f"Calculation: {day:02d}{month:02d} * {year} = {actual_calculation}")
        print(f"Calculation Digits: {[int(d) for d in str(actual_calculation)]}")
        print(f"Birth Weekday: {birth_weekday}")
        print(f"Planetary Strength: {planetary_strength}")
        print(f"Weekday Map: {weekday_map}")
        
    except Exception as e:
        log_result("Function Test", False, f"Exception occurred: {str(e)}", str(e))
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for result in test_results if result["success"])
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Show failed tests
    failed_tests = [result for result in test_results if not result["success"]]
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"  - {test['test']}: {test['message']}")
    else:
        print("\n🎉 All tests passed!")
    
    return passed, total

if __name__ == "__main__":
    passed, total = test_planetary_strength_direct()
    
    if passed == total:
        print("\n✅ All planetary strength tests passed!")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        exit(1)