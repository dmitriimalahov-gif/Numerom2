#!/usr/bin/env python3
"""
Debug test to understand the destiny number calculation issue
"""

import sys
sys.path.append('/app/backend')

from numerology import (
    calculate_destiny_number, 
    calculate_personal_numbers, 
    parse_birth_date,
    reduce_to_single_digit_always,
    reduce_to_single_digit
)

def debug_calculation():
    print("🔍 DEBUGGING DESTINY NUMBER CALCULATION")
    print("=" * 50)
    
    birth_date = "10.01.1982"
    day, month, year = parse_birth_date(birth_date)
    
    print(f"📅 Birth Date: {birth_date}")
    print(f"📊 Parsed: day={day}, month={month}, year={year}")
    print(f"📊 Sum: {day} + {month} + {year} = {day + month + year}")
    
    # Test reduce functions
    total = day + month + year
    print(f"\n🧮 Testing reduction functions:")
    print(f"   Total: {total}")
    print(f"   reduce_to_single_digit_always({total}) = {reduce_to_single_digit_always(total)}")
    print(f"   reduce_to_single_digit({total}) = {reduce_to_single_digit(total)}")
    
    # Test destiny number function
    destiny_direct = calculate_destiny_number(day, month, year)
    print(f"\n🎯 Direct destiny calculation: {destiny_direct}")
    
    # Test full personal numbers
    personal_numbers = calculate_personal_numbers(birth_date)
    print(f"\n📋 Full personal numbers:")
    for key, value in personal_numbers.items():
        if key not in ['planetary_strength', 'calculation_details']:
            print(f"   {key}: {value}")
    
    # Check if there's a discrepancy
    if personal_numbers['destiny_number'] != destiny_direct:
        print(f"\n❌ DISCREPANCY FOUND!")
        print(f"   Direct function: {destiny_direct}")
        print(f"   Personal numbers: {personal_numbers['destiny_number']}")
    else:
        print(f"\n✅ Functions are consistent")
    
    # Manual step-by-step calculation
    print(f"\n🔢 Manual step-by-step:")
    step1 = day + month + year
    print(f"   Step 1: {day} + {month} + {year} = {step1}")
    
    step2 = sum(int(d) for d in str(step1))
    print(f"   Step 2: {' + '.join(str(step1))} = {step2}")
    
    if step2 > 9:
        step3 = sum(int(d) for d in str(step2))
        print(f"   Step 3: {' + '.join(str(step2))} = {step3}")
        final = step3
    else:
        final = step2
    
    print(f"   Final: {final}")
    
    if final in [11, 22]:
        print(f"   ❌ ERROR: Final result {final} is master number - should be reduced further!")
        final_reduced = sum(int(d) for d in str(final))
        print(f"   Should be: {final_reduced}")

if __name__ == "__main__":
    debug_calculation()