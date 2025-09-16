#!/usr/bin/env python3
"""
Direct Numerology Functions Test
Tests the numerology calculation functions directly without API calls.
"""

import sys
sys.path.append('/app/backend')

from numerology import (
    calculate_personal_numbers,
    calculate_destiny_number,
    calculate_helping_mind_number,
    calculate_ruling_number,
    reduce_to_single_digit,
    parse_birth_date
)

def test_corrected_formulas():
    """Test the corrected numerology formulas"""
    print("🧮 Testing Corrected Numerology Formulas")
    print("=" * 50)
    
    # Test case from review request: 10.01.1982
    birth_date = "10.01.1982"
    day, month, year = parse_birth_date(birth_date)
    
    print(f"Testing birth date: {birth_date}")
    print(f"Parsed: day={day}, month={month}, year={year}")
    print()
    
    # Test Destiny Number (ЧС): day + month + year as numbers (10 + 1 + 1982 = 1993 → reduce to single digit)
    destiny = calculate_destiny_number(day, month, year)
    print(f"Destiny Number calculation:")
    print(f"  {day} + {month} + {year} = {day + month + year}")
    print(f"  1993 → 1+9+9+3 = 22 (should be preserved as master number)")
    print(f"  Result: {destiny}")
    print(f"  Expected: 22")
    print(f"  ✅ CORRECT" if destiny == 22 else f"  ❌ INCORRECT")
    print()
    
    # Test Helping Mind Number (ЧУ*): day + month as numbers (10 + 1 = 11 → stays 11 as master number)
    helping_mind = calculate_helping_mind_number(day, month)
    print(f"Helping Mind Number calculation:")
    print(f"  {day} + {month} = {day + month}")
    print(f"  11 (should be preserved as master number)")
    print(f"  Result: {helping_mind}")
    print(f"  Expected: 11")
    print(f"  ✅ CORRECT" if helping_mind == 11 else f"  ❌ INCORRECT")
    print()
    
    # Test Ruling Number (ПЧ): sum of ALL digits (1+0+0+1+1+9+8+2 = 22 → stays 22 as master number)
    ruling = calculate_ruling_number(day, month, year)
    all_digits = [int(d) for d in str(day) + str(month) + str(year)]
    print(f"Ruling Number calculation:")
    print(f"  All digits from {day}{month:02d}{year}: {all_digits}")
    print(f"  Sum: {sum(all_digits)} = 22 (should be preserved as master number)")
    print(f"  Result: {ruling}")
    print(f"  Expected: 22")
    print(f"  ✅ CORRECT" if ruling == 22 else f"  ❌ INCORRECT")
    print()
    
    # Test the full personal numbers calculation
    print("Full Personal Numbers calculation:")
    personal_numbers = calculate_personal_numbers(birth_date)
    print(f"  Soul Number: {personal_numbers['soul_number']}")
    print(f"  Mind Number: {personal_numbers['mind_number']}")
    print(f"  Destiny Number: {personal_numbers['destiny_number']} (expected: 22)")
    print(f"  Helping Mind Number: {personal_numbers['helping_mind_number']} (expected: 11)")
    print(f"  Wisdom Number: {personal_numbers['wisdom_number']}")
    print(f"  Ruling Number: {personal_numbers['ruling_number']} (expected: 22)")
    print()
    
    # Test reduce_to_single_digit function with various numbers
    print("Testing reduce_to_single_digit function:")
    test_cases = [
        (1993, 22, "1993 → 1+9+9+3 = 22 (preserve master)"),
        (38, 11, "38 → 3+8 = 11 (preserve master)"),
        (29, 11, "29 → 2+9 = 11 (preserve master)"),
        (47, 11, "47 → 4+7 = 11 (preserve master)"),
        (56, 11, "56 → 5+6 = 11 (preserve master)"),
        (65, 11, "65 → 6+5 = 11 (preserve master)"),
        (74, 11, "74 → 7+4 = 11 (preserve master)"),
        (83, 11, "83 → 8+3 = 11 (preserve master)"),
        (92, 11, "92 → 9+2 = 11 (preserve master)"),
        (49, 4, "49 → 4+9 = 13 → 1+3 = 4 (reduce normally)"),
        (123, 6, "123 → 1+2+3 = 6 (reduce normally)")
    ]
    
    for number, expected, description in test_cases:
        result = reduce_to_single_digit(number)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description} → Result: {result}")
    
    print()
    print("=" * 50)
    
    # Summary
    correct_destiny = personal_numbers['destiny_number'] == 22
    correct_helping_mind = personal_numbers['helping_mind_number'] == 11
    correct_ruling = personal_numbers['ruling_number'] == 22
    
    all_correct = correct_destiny and correct_helping_mind and correct_ruling
    
    print("SUMMARY:")
    print(f"✅ Destiny Number: {'CORRECT' if correct_destiny else 'INCORRECT'}")
    print(f"✅ Helping Mind Number: {'CORRECT' if correct_helping_mind else 'INCORRECT'}")
    print(f"✅ Ruling Number: {'CORRECT' if correct_ruling else 'INCORRECT'}")
    print()
    print(f"🎯 Overall Result: {'ALL TESTS PASSED' if all_correct else 'SOME TESTS FAILED'}")
    
    return all_correct

if __name__ == "__main__":
    success = test_corrected_formulas()
    exit(0 if success else 1)