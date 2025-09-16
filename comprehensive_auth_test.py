#!/usr/bin/env python3
"""
COMPREHENSIVE AUTHENTICATION AND ACCESS RIGHTS TEST
Based on review request requirements
"""

import requests
import json
import uuid
from datetime import datetime

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def test_super_admin_scenario():
    """1. ТЕСТ СУПЕР АДМИНИСТРАТОРА"""
    print("=" * 60)
    print("1. ТЕСТ СУПЕР АДМИНИСТРАТОРА")
    print("=" * 60)
    
    results = []
    
    # Super admin credentials
    creds = {
        "email": "dmitrii.malahov@gmail.com",
        "password": "756bvy67H"
    }
    
    try:
        # Test login
        print(f"🔐 Testing login for {creds['email']}...")
        response = requests.post(f"{BACKEND_URL}/auth/login", json=creds, timeout=60)
        
        if response.status_code != 200:
            results.append(("❌", "Super Admin Login", f"Failed with status {response.status_code}: {response.text}"))
            return results
        
        data = response.json()
        token = data.get('access_token')
        user = data.get('user', {})
        
        if not token:
            results.append(("❌", "Super Admin Login", "No access token received"))
            return results
        
        # Check is_super_admin = true
        is_super_admin = user.get('is_super_admin', False)
        if is_super_admin:
            results.append(("✅", "Super Admin Login", f"Successfully logged in with is_super_admin=True, Credits: {user.get('credits_remaining')}"))
        else:
            results.append(("❌", "Super Admin Rights", f"is_super_admin={is_super_admin}, expected True"))
            return results
        
        # Test admin endpoints
        admin_endpoints = [
            ("/admin/users", "GET", "Admin Users List"),
            ("/admin/materials", "GET", "Admin Materials List"),
        ]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        for endpoint, method, description in admin_endpoints:
            try:
                print(f"🔧 Testing {description}...")
                admin_response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=30)
                
                if admin_response.status_code == 200:
                    admin_data = admin_response.json()
                    if endpoint == "/admin/users":
                        users = admin_data.get('users', [])
                        results.append(("✅", f"Super Admin Access - {description}", f"Successfully accessed, found {len(users)} users"))
                    elif endpoint == "/admin/materials":
                        materials = admin_data.get('materials', [])
                        results.append(("✅", f"Super Admin Access - {description}", f"Successfully accessed, found {len(materials)} materials"))
                else:
                    results.append(("❌", f"Super Admin Access - {description}", f"Access denied with status {admin_response.status_code}"))
                    
            except Exception as e:
                results.append(("❌", f"Super Admin Access - {description}", f"Request failed: {str(e)}"))
        
        # Test video upload endpoint
        try:
            print("🎥 Testing video upload endpoint...")
            files = {'file': ('test.mp4', b'mock video content for testing', 'video/mp4')}
            upload_response = requests.post(f"{BACKEND_URL}/admin/upload-video", files=files, headers=headers, timeout=30)
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                results.append(("✅", "Super Admin Access - Video Upload", f"Successfully uploaded video, ID: {upload_data.get('video_id')}"))
            else:
                results.append(("❌", "Super Admin Access - Video Upload", f"Upload failed with status {upload_response.status_code}"))
                
        except Exception as e:
            results.append(("❌", "Super Admin Access - Video Upload", f"Request failed: {str(e)}"))
        
    except Exception as e:
        results.append(("❌", "Super Admin Login", f"Request failed: {str(e)}"))
    
    return results

def test_regular_user_scenario():
    """2. ТЕСТ ОБЫЧНОГО ПОЛЬЗОВАТЕЛЯ"""
    print("=" * 60)
    print("2. ТЕСТ ОБЫЧНОГО ПОЛЬЗОВАТЕЛЯ")
    print("=" * 60)
    
    results = []
    
    # Create test user
    test_user = {
        "email": f"testuser_{uuid.uuid4().hex[:8]}@test.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "birth_date": "01.01.1990",
        "city": "Москва"
    }
    
    try:
        # Register user
        print(f"👤 Registering test user {test_user['email']}...")
        response = requests.post(f"{BACKEND_URL}/auth/register", json=test_user, timeout=30)
        
        if response.status_code != 200:
            results.append(("❌", "Regular User Registration", f"Failed with status {response.status_code}: {response.text}"))
            return results
        
        data = response.json()
        token = data.get('access_token')
        user = data.get('user', {})
        
        if not token:
            results.append(("❌", "Regular User Registration", "No access token received"))
            return results
        
        # Check is_super_admin = false or absent
        is_super_admin = user.get('is_super_admin', False)
        if not is_super_admin:
            results.append(("✅", "Regular User Registration", f"Successfully registered with is_super_admin=False"))
        else:
            results.append(("❌", "Regular User Rights", f"is_super_admin={is_super_admin}, expected False"))
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test access to regular functions
        regular_endpoints = [
            ("/user/profile", "GET", "User Profile"),
        ]
        
        for endpoint, method, description in regular_endpoints:
            try:
                print(f"🔧 Testing {description}...")
                reg_response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=30)
                
                if reg_response.status_code == 200:
                    results.append(("✅", f"Regular User Access - {description}", "Successfully accessed"))
                else:
                    results.append(("❌", f"Regular User Access - {description}", f"Failed with status {reg_response.status_code}"))
                    
            except Exception as e:
                results.append(("❌", f"Regular User Access - {description}", f"Request failed: {str(e)}"))
        
        # Test numerology endpoints (may fail due to credits)
        try:
            print("🔢 Testing numerology endpoint...")
            num_response = requests.post(f"{BACKEND_URL}/numerology/personal-numbers", 
                                       json={"birth_date": "15.03.1990"}, headers=headers, timeout=30)
            
            if num_response.status_code in [200, 402]:  # 402 = insufficient credits is OK
                results.append(("✅", "Regular User Access - Numerology", f"Endpoint accessible (status: {num_response.status_code})"))
            else:
                results.append(("❌", "Regular User Access - Numerology", f"Unexpected status {num_response.status_code}"))
                
        except Exception as e:
            results.append(("❌", "Regular User Access - Numerology", f"Request failed: {str(e)}"))
        
        # Test ОТСУТСТВИЕ доступа к админ endpoints (должно быть 403)
        admin_endpoints = [
            ("/admin/users", "GET", "Admin Users List"),
            ("/admin/materials", "GET", "Admin Materials List"),
        ]
        
        for endpoint, method, description in admin_endpoints:
            try:
                print(f"🚫 Testing admin block for {description}...")
                admin_response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=30)
                
                if admin_response.status_code == 403:
                    results.append(("✅", f"Regular User Admin Block - {description}", "Correctly blocked with 403"))
                else:
                    results.append(("❌", f"Regular User Admin Block - {description}", f"Should be 403 but got {admin_response.status_code}"))
                    
            except Exception as e:
                results.append(("❌", f"Regular User Admin Block - {description}", f"Request failed: {str(e)}"))
        
    except Exception as e:
        results.append(("❌", "Regular User Registration", f"Request failed: {str(e)}"))
    
    return results

def test_security_scenarios():
    """3. ТЕСТ БЕЗОПАСНОСТИ"""
    print("=" * 60)
    print("3. ТЕСТ БЕЗОПАСНОСТИ")
    print("=" * 60)
    
    results = []
    
    admin_endpoints = [
        ("/admin/users", "GET", "Admin Users"),
        ("/admin/materials", "GET", "Admin Materials"),
    ]
    
    for endpoint, method, description in admin_endpoints:
        # Test without token
        try:
            print(f"🔒 Testing {description} without token...")
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=30)
            
            if response.status_code in [401, 403]:  # Both are acceptable for security
                results.append(("✅", f"Security - No Token - {description}", f"Correctly rejected (status: {response.status_code})"))
            else:
                results.append(("❌", f"Security - No Token - {description}", f"Should reject but got {response.status_code}"))
                
        except Exception as e:
            results.append(("❌", f"Security - No Token - {description}", f"Request failed: {str(e)}"))
        
        # Test with invalid token
        try:
            print(f"🔒 Testing {description} with invalid token...")
            headers = {"Authorization": "Bearer invalid_token_123"}
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=30)
            
            if response.status_code == 401:
                results.append(("✅", f"Security - Invalid Token - {description}", "Correctly rejected invalid token (401)"))
            else:
                results.append(("❌", f"Security - Invalid Token - {description}", f"Should be 401 but got {response.status_code}"))
                
        except Exception as e:
            results.append(("❌", f"Security - Invalid Token - {description}", f"Request failed: {str(e)}"))
    
    return results

def main():
    """Run all authentication and access tests"""
    print("🔐 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ВХОДА И ПРАВ ДОСТУПА")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    all_results = []
    
    # Run all test scenarios
    all_results.extend(test_super_admin_scenario())
    all_results.extend(test_regular_user_scenario())
    all_results.extend(test_security_scenarios())
    
    # Print results
    print("=" * 80)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ / TEST RESULTS")
    print("=" * 80)
    
    for status, test_name, message in all_results:
        print(f"{status} {test_name}")
        print(f"   {message}")
        print()
    
    # Summary
    print("=" * 80)
    print("ИТОГИ / SUMMARY")
    print("=" * 80)
    
    total_tests = len(all_results)
    passed_tests = len([r for r in all_results if r[0] == "✅"])
    failed_tests = total_tests - passed_tests
    
    print(f"Всего тестов / Total tests: {total_tests}")
    print(f"Пройдено / Passed: {passed_tests}")
    print(f"Провалено / Failed: {failed_tests}")
    print(f"Успешность / Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Система входа и прав доступа работает корректно")
    else:
        print(f"\n⚠️  {failed_tests} тестов провалились")
        print("❌ Требуется исправление системы безопасности")
    
    return failed_tests == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)