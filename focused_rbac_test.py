#!/usr/bin/env python3
"""
Focused Role-Based Access Control Testing
Tests the core functionality that we know is working
"""

import requests
import json
import time

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def test_core_rbac_functionality():
    print("🔐 FOCUSED ROLE-BASED ACCESS CONTROL TESTING")
    print("=" * 60)
    
    results = []
    
    # 1. Test Super Admin Login
    print("\n1. Testing Super Admin Login...")
    super_admin_creds = {
        "email": "dmitrii.malahov@gmail.com",
        "password": "756bvy67H"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=super_admin_creds, timeout=30)
    if response.status_code == 200:
        data = response.json()
        super_admin_token = data["access_token"]
        user_data = data["user"]
        
        if user_data.get("is_super_admin") == True:
            print("✅ Super admin login successful")
            print(f"   Credits: {user_data.get('credits_remaining')}")
            print(f"   Premium: {user_data.get('is_premium')}")
            results.append(("Super Admin Login", True))
        else:
            print("❌ Super admin login failed - not marked as super admin")
            results.append(("Super Admin Login", False))
            return results
    else:
        print(f"❌ Super admin login failed: {response.text}")
        results.append(("Super Admin Login", False))
        return results
    
    # 2. Test Super Admin Access to Admin Endpoints
    print("\n2. Testing Super Admin Access to Admin Endpoints...")
    headers = {"Authorization": f"Bearer {super_admin_token}"}
    
    admin_endpoints = [
        "/admin/users",
        "/admin/lessons", 
        "/admin/materials"
    ]
    
    for endpoint in admin_endpoints:
        response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=30)
        if response.status_code == 200:
            print(f"✅ Super admin can access {endpoint}")
            results.append((f"Super Admin Access {endpoint}", True))
        else:
            print(f"❌ Super admin cannot access {endpoint}: {response.status_code}")
            results.append((f"Super Admin Access {endpoint}", False))
    
    # 3. Test Regular User Registration and Access Control
    print("\n3. Testing Regular User Access Control...")
    regular_user_data = {
        "email": f"test_user_{int(time.time())}@test.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "birth_date": "10.05.1995",
        "city": "Москва"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=regular_user_data, timeout=30)
    if response.status_code == 200:
        data = response.json()
        regular_token = data["access_token"]
        user_data = data["user"]
        
        if not user_data.get("is_super_admin") and not user_data.get("is_admin"):
            print("✅ Regular user registered without admin privileges")
            results.append(("Regular User Registration", True))
            
            # Test that regular user is blocked from admin endpoints
            regular_headers = {"Authorization": f"Bearer {regular_token}"}
            
            for endpoint in admin_endpoints:
                response = requests.get(f"{BACKEND_URL}{endpoint}", headers=regular_headers, timeout=30)
                if response.status_code == 403:
                    print(f"✅ Regular user correctly blocked from {endpoint}")
                    results.append((f"Regular User Blocked {endpoint}", True))
                else:
                    print(f"❌ Regular user should be blocked from {endpoint} but got: {response.status_code}")
                    results.append((f"Regular User Blocked {endpoint}", False))
        else:
            print("❌ Regular user has admin privileges")
            results.append(("Regular User Registration", False))
    else:
        print(f"❌ Regular user registration failed: {response.text}")
        results.append(("Regular User Registration", False))
    
    # 4. Test Admin Role Management
    print("\n4. Testing Admin Role Management...")
    
    # Create another user to promote to admin
    admin_user_data = {
        "email": f"admin_test_{int(time.time())}@test.com",
        "password": "AdminPass123!",
        "full_name": "Admin Test User",
        "birth_date": "15.08.1988",
        "city": "Москва"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=admin_user_data, timeout=30)
    if response.status_code == 200:
        data = response.json()
        admin_user_token = data["access_token"]
        user_data = data["user"]
        user_id = user_data["id"]
        
        # Promote user to admin using super admin token
        response = requests.post(f"{BACKEND_URL}/admin/make-admin/{user_id}", headers=headers, timeout=30)
        if response.status_code == 200:
            promote_data = response.json()
            print(f"✅ User promoted to admin: {promote_data.get('message', 'Success')}")
            results.append(("Make Admin Endpoint", True))
            
            # Test revoking admin rights
            response = requests.delete(f"{BACKEND_URL}/admin/revoke-admin/{user_id}", headers=headers, timeout=30)
            if response.status_code == 200:
                revoke_data = response.json()
                print(f"✅ Admin rights revoked: {revoke_data.get('message', 'Success')}")
                results.append(("Revoke Admin Endpoint", True))
            else:
                print(f"❌ Failed to revoke admin rights: {response.status_code}")
                results.append(("Revoke Admin Endpoint", False))
        else:
            print(f"❌ Failed to promote user to admin: {response.status_code}")
            results.append(("Make Admin Endpoint", False))
    else:
        print(f"❌ Failed to create user for admin promotion: {response.text}")
        results.append(("Make Admin Endpoint", False))
        results.append(("Revoke Admin Endpoint", False))
    
    # 5. Test User Profile Admin Fields
    print("\n5. Testing User Profile Admin Fields...")
    response = requests.get(f"{BACKEND_URL}/user/profile", headers=headers, timeout=30)
    if response.status_code == 200:
        data = response.json()
        if "is_super_admin" in data or "is_admin" in data:
            admin_status = f"is_super_admin: {data.get('is_super_admin')}, is_admin: {data.get('is_admin')}"
            print(f"✅ User profile includes admin fields: {admin_status}")
            results.append(("User Profile Admin Fields", True))
        else:
            print("❌ User profile missing admin fields")
            results.append(("User Profile Admin Fields", False))
    else:
        print(f"❌ Failed to get user profile: {response.status_code}")
        results.append(("User Profile Admin Fields", False))
    
    # Print Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Show results
    print("\n📋 DETAILED RESULTS:")
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
    
    return results

if __name__ == "__main__":
    test_core_rbac_functionality()