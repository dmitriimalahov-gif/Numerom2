#!/usr/bin/env python3
"""
System diagnostic test for NUMEROM - Quick verification of core functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"

def test_system():
    print("🎯 NUMEROM SYSTEM DIAGNOSTIC")
    print("=" * 50)
    
    session = requests.Session()
    session.timeout = 5  # 5 second timeout
    
    results = []
    
    # Test 1: Authentication
    print("1. Testing authentication...")
    try:
        login_data = {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            user = data.get('user')
            
            if token and user:
                print(f"✅ Authentication: SUCCESS - User ID: {user.get('id')}, Super Admin: {user.get('is_super_admin')}")
                session.headers.update({'Authorization': f'Bearer {token}'})
                results.append(("Authentication", "PASS", f"User: {user.get('email')}, Credits: {user.get('credits_remaining')}"))
            else:
                print("❌ Authentication: FAIL - No token or user data")
                results.append(("Authentication", "FAIL", "No token or user data"))
                return results
        else:
            print(f"❌ Authentication: FAIL - HTTP {response.status_code}")
            results.append(("Authentication", "FAIL", f"HTTP {response.status_code}"))
            return results
    except Exception as e:
        print(f"❌ Authentication: ERROR - {str(e)}")
        results.append(("Authentication", "FAIL", str(e)))
        return results
    
    # Test 2: Personal Numbers
    print("2. Testing personal numbers...")
    try:
        response = session.post(f"{BACKEND_URL}/numerology/personal-numbers")
        if response.status_code == 200:
            data = response.json()
            if 'soul_number' in data:
                print(f"✅ Personal Numbers: SUCCESS - Soul: {data.get('soul_number')}, Destiny: {data.get('destiny_number')}")
                results.append(("Personal Numbers", "PASS", f"Soul: {data.get('soul_number')}, Destiny: {data.get('destiny_number')}"))
            else:
                print("❌ Personal Numbers: FAIL - Missing data")
                results.append(("Personal Numbers", "FAIL", "Missing data"))
        elif response.status_code == 402:
            print("⚠️ Personal Numbers: WARN - Insufficient credits")
            results.append(("Personal Numbers", "WARN", "Insufficient credits"))
        else:
            print(f"❌ Personal Numbers: FAIL - HTTP {response.status_code}")
            results.append(("Personal Numbers", "FAIL", f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ Personal Numbers: ERROR - {str(e)}")
        results.append(("Personal Numbers", "FAIL", str(e)))
    
    # Test 3: Pythagorean Square
    print("3. Testing Pythagorean square...")
    try:
        response = session.post(f"{BACKEND_URL}/numerology/pythagorean-square")
        if response.status_code == 200:
            data = response.json()
            if 'square' in data:
                additional = data.get('additional_numbers', [])
                print(f"✅ Pythagorean Square: SUCCESS - Additional numbers: {additional}")
                results.append(("Pythagorean Square", "PASS", f"Additional numbers: {additional}"))
            else:
                print("❌ Pythagorean Square: FAIL - Missing square data")
                results.append(("Pythagorean Square", "FAIL", "Missing square data"))
        elif response.status_code == 402:
            print("⚠️ Pythagorean Square: WARN - Insufficient credits")
            results.append(("Pythagorean Square", "WARN", "Insufficient credits"))
        else:
            print(f"❌ Pythagorean Square: FAIL - HTTP {response.status_code}")
            results.append(("Pythagorean Square", "FAIL", f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ Pythagorean Square: ERROR - {str(e)}")
        results.append(("Pythagorean Square", "FAIL", str(e)))
    
    # Test 4: HTML Report Generation
    print("4. Testing HTML report generation...")
    try:
        html_request = {
            "selected_calculations": ["personal_numbers", "pythagorean_square"],
            "theme": "light"
        }
        response = session.post(f"{BACKEND_URL}/reports/html/numerology", json=html_request)
        
        if response.status_code == 200:
            html_content = response.text
            if 'text/html' in response.headers.get('content-type', ''):
                size = len(html_content)
                has_numerom = 'NUMEROM' in html_content
                print(f"✅ HTML Report: SUCCESS - Size: {size} chars, Has NUMEROM: {has_numerom}")
                results.append(("HTML Report", "PASS", f"Size: {size} chars, NUMEROM: {has_numerom}"))
            else:
                print("❌ HTML Report: FAIL - Wrong content type")
                results.append(("HTML Report", "FAIL", "Wrong content type"))
        elif response.status_code == 402:
            print("⚠️ HTML Report: WARN - Insufficient credits")
            results.append(("HTML Report", "WARN", "Insufficient credits"))
        else:
            print(f"❌ HTML Report: FAIL - HTTP {response.status_code}")
            results.append(("HTML Report", "FAIL", f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ HTML Report: ERROR - {str(e)}")
        results.append(("HTML Report", "FAIL", str(e)))
    
    # Test 5: Admin Functions (if super admin)
    print("5. Testing admin functions...")
    try:
        response = session.get(f"{BACKEND_URL}/admin/users")
        if response.status_code == 200:
            data = response.json()
            if 'users' in data:
                user_count = len(data['users'])
                print(f"✅ Admin Users: SUCCESS - Found {user_count} users")
                results.append(("Admin Users", "PASS", f"{user_count} users"))
            else:
                print("❌ Admin Users: FAIL - Wrong response structure")
                results.append(("Admin Users", "FAIL", "Wrong response structure"))
        elif response.status_code == 403:
            print("⚠️ Admin Users: SKIP - Not super admin")
            results.append(("Admin Users", "SKIP", "Not super admin"))
        else:
            print(f"❌ Admin Users: FAIL - HTTP {response.status_code}")
            results.append(("Admin Users", "FAIL", f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ Admin Users: ERROR - {str(e)}")
        results.append(("Admin Users", "FAIL", str(e)))
    
    # Test 6: Materials
    print("6. Testing materials...")
    try:
        response = session.get(f"{BACKEND_URL}/materials")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                material_count = len(data)
                print(f"✅ Materials: SUCCESS - Found {material_count} materials")
                results.append(("Materials", "PASS", f"{material_count} materials"))
            else:
                print("❌ Materials: FAIL - Wrong response structure")
                results.append(("Materials", "FAIL", "Wrong response structure"))
        else:
            print(f"❌ Materials: FAIL - HTTP {response.status_code}")
            results.append(("Materials", "FAIL", f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ Materials: ERROR - {str(e)}")
        results.append(("Materials", "FAIL", str(e)))
    
    return results

def main():
    results = test_system()
    
    print("\n" + "=" * 50)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    passed = len([r for r in results if r[1] == "PASS"])
    failed = len([r for r in results if r[1] == "FAIL"])
    warned = len([r for r in results if r[1] == "WARN"])
    skipped = len([r for r in results if r[1] == "SKIP"])
    
    print(f"Total tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️ Warnings: {warned}")
    print(f"⏭️ Skipped: {skipped}")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for test, status, details in results:
            if status == "FAIL":
                print(f"  • {test}: {details}")
    
    # Critical assessment
    critical_failures = [r for r in results if r[1] == "FAIL" and r[0] in ["Authentication", "Personal Numbers", "Pythagorean Square"]]
    
    if critical_failures:
        print(f"\n🚨 CRITICAL ISSUES FOUND: {len(critical_failures)}")
        print("System has serious problems!")
        return 1
    else:
        print("\n🎉 NO CRITICAL ISSUES FOUND")
        if failed == 0:
            print("✅ SYSTEM IS WORKING CORRECTLY!")
        else:
            print("⚠️ System is working with minor issues.")
        return 0

if __name__ == "__main__":
    sys.exit(main())