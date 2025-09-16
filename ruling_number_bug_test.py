#!/usr/bin/env python3
"""
Simple test to demonstrate the ruling number bug
"""

import sys
sys.path.append('/app/backend')

from numerology import calculate_ruling_number

def test_ruling_number_bug():
    print("Testing ruling number calculation bug:")
    print()
    
    # Test case: 02.09.1998
    # Digits: 0+2+0+9+1+9+9+8 = 38
    # Should reduce: 38 → 3+8 = 11 (and stop here, preserving master number 11)
    # But current implementation continues: 11 → 1+1 = 2
    
    day, month, year = 2, 9, 1998
    result = calculate_ruling_number(day, month, year)
    
    print(f"Birth date: {day:02d}.{month:02d}.{year}")
    print(f"Digits: 0+2+0+9+1+9+9+8 = 38")
    print(f"Expected: 38 → 3+8 = 11 (preserve master number)")
    print(f"Actual result: {result}")
    
    if result == 11:
        print("✅ PASS: Master number 11 preserved correctly")
        return True
    else:
        print("❌ FAIL: Master number 11 not preserved")
        print("🐛 BUG: Algorithm only checks for 11/22 at initial sum, not during reduction")
        return False

if __name__ == "__main__":
    success = test_ruling_number_bug()
    exit(0 if success else 1)