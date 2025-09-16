#!/usr/bin/env python3
"""
Focused test for Super Admin Auto-Seed Login functionality
Tests the specific issue mentioned in test_result.md
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class SuperAdminTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_super_admin_login(self):
        """Test Super Admin login with credentials from auth.py"""
        print(f"🔐 Testing Super Admin login...")
        print(f"   Email: {SUPER_ADMIN_EMAIL}")
        print(f"   Password: {SUPER_ADMIN_PASSWORD}")
        
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_text = await response.text()
                print(f"   Status: {response.status}")
                print(f"   Response: {response_text[:200]}...")
                
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    user_info = data.get("user", {})
                    
                    print(f"✅ LOGIN SUCCESS")
                    print(f"   User ID: {user_info.get('id')}")
                    print(f"   Full Name: {user_info.get('full_name')}")
                    print(f"   Is Super Admin: {user_info.get('is_super_admin')}")
                    print(f"   Is Premium: {user_info.get('is_premium')}")
                    print(f"   Credits: {user_info.get('credits_remaining')}")
                    
                    return True, data
                else:
                    print(f"❌ LOGIN FAILED")
                    print(f"   Error: {response_text}")
                    return False, response_text
                    
        except Exception as e:
            print(f"❌ LOGIN ERROR: {str(e)}")
            return False, str(e)
    
    async def test_admin_lessons_access(self):
        """Test admin access to lessons endpoint"""
        if not self.auth_token:
            print("❌ No auth token available for admin test")
            return False, "No auth token"
            
        print(f"🔑 Testing admin access to GET /api/admin/lessons...")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(
                f"{BACKEND_URL}/admin/lessons",
                headers=headers
            ) as response:
                response_text = await response.text()
                print(f"   Status: {response.status}")
                print(f"   Response: {response_text[:200]}...")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ ADMIN ACCESS SUCCESS")
                    print(f"   Lessons count: {len(data) if isinstance(data, list) else 'N/A'}")
                    return True, data
                else:
                    print(f"❌ ADMIN ACCESS FAILED")
                    print(f"   Error: {response_text}")
                    return False, response_text
                    
        except Exception as e:
            print(f"❌ ADMIN ACCESS ERROR: {str(e)}")
            return False, str(e)
    
    async def run_complete_test(self):
        """Run the complete super admin test sequence"""
        print("=" * 60)
        print("SUPER ADMIN AUTO-SEED LOGIN TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step 1: Test login
        login_success, login_result = await self.test_super_admin_login()
        print()
        
        # Step 2: Test admin access (only if login succeeded)
        admin_success = False
        admin_result = None
        
        if login_success:
            admin_success, admin_result = await self.test_admin_lessons_access()
            print()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"1. Super Admin Login: {'✅ PASS' if login_success else '❌ FAIL'}")
        print(f"2. Admin Lessons Access: {'✅ PASS' if admin_success else '❌ FAIL' if login_success else '⏭️ SKIPPED'}")
        print()
        
        if login_success and admin_success:
            print("🎉 ALL TESTS PASSED - Super Admin auto-seed is working correctly!")
            return True
        elif login_success and not admin_success:
            print("⚠️ PARTIAL SUCCESS - Login works but admin access failed")
            return False
        else:
            print("💥 CRITICAL FAILURE - Super Admin login is not working")
            return False

async def main():
    """Main test execution"""
    async with SuperAdminTester() as tester:
        success = await tester.run_complete_test()
        return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)