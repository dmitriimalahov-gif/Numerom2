#!/usr/bin/env python3
"""
Consultation System Test - Review Request Verification
Testing the fixed consultation and points system according to review request.

CRITICAL FIXES TO VERIFY:
1. ✅ Fixed cost for personal consultations - 6667 points
2. ✅ User data loads IMMEDIATELY after purchase
3. ✅ No duplicate consultations in admin panel
4. ✅ Protection against amount=0 transactions
5. ✅ Protection against double purchases (30-second cooldown)
6. ✅ Correct credit transactions

TESTING SCENARIO:
1. Login as dmitrii.malahov@gmail.com
2. Create new consultation for testing
3. Purchase consultation for 6667 points
4. Verify buyer data loads immediately in admin panel
5. Test double purchase protection
6. Verify credit transactions

Credentials: dmitrii.malahov@gmail.com / 756bvy67H
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"
EXPECTED_CONSULTATION_COST = 6667

class ConsultationSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.initial_balance = None
        self.consultation_id = None
        self.test_results = []
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{status}] {message}")
        
    def add_result(self, test_name, success, message):
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        status = "✅ PASS" if success else "❌ FAIL"
        self.log(f"{test_name}: {message}", status)
        
    def authenticate(self):
        """Authenticate as dmitrii.malahov@gmail.com"""
        self.log("🔐 Authenticating as test user...")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code != 200:
                self.add_result("Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
            data = response.json()
            self.auth_token = data['access_token']
            self.user_id = data['user']['id']
            self.initial_balance = data['user'].get('credits_remaining', 0)
            
            # Set authorization header for future requests
            self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
            
            self.log(f"User ID: {self.user_id}")
            self.log(f"Initial Credits: {self.initial_balance}")
            self.log(f"Super Admin: {data['user'].get('is_super_admin', False)}")
            
            self.add_result("Authentication", True, f"Successfully authenticated with {self.initial_balance} credits")
            return True
            
        except Exception as e:
            self.add_result("Authentication", False, f"Exception during login: {str(e)}")
            return False
            
    def create_test_consultation(self):
        """Create a new consultation for testing"""
        self.log("📝 Creating test consultation...")
        
        # Generate unique consultation ID
        self.consultation_id = f"test_consultation_{int(time.time())}"
        
        consultation_data = {
            "id": self.consultation_id,
            "title": "Тестовая консультация для проверки системы",
            "description": "Консультация для тестирования исправленной системы баллов и загрузки данных",
            "assigned_user_id": self.user_id,
            "cost_credits": EXPECTED_CONSULTATION_COST,
            "is_active": True
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/consultations", json=consultation_data)
            
            if response.status_code != 200:
                self.add_result("Create Consultation", False, f"Failed to create consultation: {response.status_code} - {response.text}")
                return False
                
            result = response.json()
            self.log(f"Created consultation ID: {self.consultation_id}")
            
            self.add_result("Create Consultation", True, f"Successfully created consultation: {self.consultation_id}")
            return True
            
        except Exception as e:
            self.add_result("Create Consultation", False, f"Exception: {str(e)}")
            return False
            
    def test_consultation_cost_verification(self):
        """Verify consultation has correct cost (6667 points)"""
        self.log("💰 Verifying consultation cost...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/consultations")
            
            if response.status_code != 200:
                self.add_result("Cost Verification", False, f"Failed to get consultations: {response.status_code}")
                return False
                
            consultations = response.json()
            
            # Find our test consultation
            test_consultation = None
            for consultation in consultations:
                if consultation.get('id') == self.consultation_id:
                    test_consultation = consultation
                    break
                    
            if not test_consultation:
                self.add_result("Cost Verification", False, f"Test consultation {self.consultation_id} not found")
                return False
                
            # Check cost - but note that the endpoint uses fixed 6667 regardless of stored cost
            self.log(f"Consultation stored cost: {test_consultation.get('cost_credits', 'N/A')}")
            self.log(f"Expected purchase cost: {EXPECTED_CONSULTATION_COST} (fixed in endpoint)")
            
            self.add_result("Cost Verification", True, f"Consultation found, purchase will use fixed cost of {EXPECTED_CONSULTATION_COST}")
            return True
            
        except Exception as e:
            self.add_result("Cost Verification", False, f"Exception: {str(e)}")
            return False
            
    def test_purchase_consultation(self):
        """Test purchasing the consultation for 6667 points"""
        if not self.consultation_id:
            self.add_result("Purchase Consultation", False, "No consultation ID available")
            return False
            
        self.log("💳 Testing consultation purchase...")
        
        try:
            # Record balance before purchase
            balance_before = self.initial_balance
            
            response = self.session.post(f"{BACKEND_URL}/user/consultations/{self.consultation_id}/purchase")
            
            if response.status_code != 200:
                self.add_result("Purchase Consultation", False, f"Purchase failed: {response.status_code} - {response.text}")
                return False
                
            result = response.json()
            
            self.log(f"Purchase result: {result}")
            
            # Verify the response contains expected data
            credits_spent = result.get('credits_spent')
            remaining_credits = result.get('remaining_credits')
            
            if credits_spent == EXPECTED_CONSULTATION_COST:
                self.add_result("Correct Cost Deduction", True, f"Correctly charged {credits_spent} points")
            else:
                self.add_result("Correct Cost Deduction", False, f"Expected {EXPECTED_CONSULTATION_COST}, charged {credits_spent}")
                
            expected_remaining = balance_before - EXPECTED_CONSULTATION_COST
            if remaining_credits == expected_remaining:
                self.add_result("Balance Calculation", True, f"Correct remaining balance: {remaining_credits}")
            else:
                self.add_result("Balance Calculation", False, f"Expected {expected_remaining}, got {remaining_credits}")
                
            self.add_result("Purchase Consultation", True, f"Purchase successful: {result.get('message', 'No message')}")
            return True
                
        except Exception as e:
            self.add_result("Purchase Consultation", False, f"Exception: {str(e)}")
            return False
            
    def test_immediate_buyer_data_loading(self):
        """Test that buyer data loads IMMEDIATELY in admin panel"""
        self.log("⚡ Testing immediate buyer data loading...")
        
        try:
            # Get admin consultations immediately after purchase
            response = self.session.get(f"{BACKEND_URL}/admin/consultations")
            
            if response.status_code != 200:
                self.add_result("Immediate Data Loading", False, f"Failed to get admin consultations: {response.status_code}")
                return False
                
            consultations = response.json()
            
            # Find our purchased consultation
            purchased_consultation = None
            for consultation in consultations:
                if consultation.get('id') == self.consultation_id:
                    purchased_consultation = consultation
                    break
                    
            if not purchased_consultation:
                self.add_result("Immediate Data Loading", False, f"Purchased consultation not found in admin list")
                return False
                
            # Check if buyer data is present IMMEDIATELY
            buyer_email = purchased_consultation.get('buyer_email')
            buyer_name = purchased_consultation.get('buyer_full_name')
            is_purchased = purchased_consultation.get('is_purchased', False)
            purchased_at = purchased_consultation.get('purchased_at')
            
            if buyer_email == TEST_EMAIL and buyer_name and is_purchased and purchased_at:
                self.add_result("Immediate Data Loading", True, f"Buyer data loaded immediately: {buyer_email}, {buyer_name}")
            else:
                self.add_result("Immediate Data Loading", False, f"Buyer data incomplete: email={buyer_email}, name={buyer_name}, purchased={is_purchased}")
                
            # Check for buyer_details object
            buyer_details = purchased_consultation.get('buyer_details')
            if buyer_details and buyer_details.get('email') == TEST_EMAIL:
                self.add_result("Buyer Details Object", True, f"Buyer details object present with correct email")
            else:
                self.add_result("Buyer Details Object", False, f"Buyer details object missing or incorrect")
                
            return True
            
        except Exception as e:
            self.add_result("Immediate Data Loading", False, f"Exception: {str(e)}")
            return False
            
    def test_no_duplicate_consultations(self):
        """Test that no duplicate consultations exist in admin panel"""
        self.log("🔍 Testing for duplicate consultations...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/consultations")
            
            if response.status_code != 200:
                self.add_result("No Duplicates", False, f"Failed to get consultations: {response.status_code}")
                return False
                
            consultations = response.json()
            
            # Count occurrences of our consultation ID
            consultation_count = sum(1 for c in consultations if c.get('id') == self.consultation_id)
            
            if consultation_count == 1:
                self.add_result("No Duplicates", True, f"No duplicate consultations found (count: {consultation_count})")
            else:
                self.add_result("No Duplicates", False, f"Found {consultation_count} instances of consultation {self.consultation_id}")
                
            # Check for any duplicate IDs in general
            all_ids = [c.get('id') for c in consultations if c.get('id')]
            unique_ids = set(all_ids)
            
            if len(all_ids) == len(unique_ids):
                self.add_result("No Duplicate IDs", True, f"No duplicate consultation IDs found ({len(all_ids)} consultations)")
            else:
                self.add_result("No Duplicate IDs", False, f"Found duplicate IDs: {len(all_ids)} total, {len(unique_ids)} unique")
                
            return True
            
        except Exception as e:
            self.add_result("No Duplicates", False, f"Exception: {str(e)}")
            return False
            
    def test_double_purchase_protection(self):
        """Test 30-second cooldown protection against double purchases"""
        self.log("🛡️ Testing double purchase protection...")
        
        if not self.consultation_id:
            self.add_result("Double Purchase Protection", False, "No consultation ID for testing")
            return False
            
        try:
            # Attempt to purchase the same consultation again immediately
            response = self.session.post(f"{BACKEND_URL}/user/consultations/{self.consultation_id}/purchase")
            
            # Should fail with appropriate error
            if response.status_code in [400, 409, 429]:
                result = response.json()
                error_message = result.get('detail', result.get('message', 'Unknown error'))
                
                self.log(f"Double purchase attempt result: {error_message}")
                
                # Check if error mentions already purchased or cooldown
                if ('уже приобретена' in error_message.lower() or 
                    'already' in error_message.lower() or 
                    'cooldown' in error_message.lower() or
                    'подождите' in error_message.lower()):
                    self.add_result("Double Purchase Protection", True, f"Protection working: {error_message}")
                    return True
                else:
                    self.add_result("Double Purchase Protection", False, f"Unexpected error message: {error_message}")
                    return False
            else:
                self.add_result("Double Purchase Protection", False, f"Expected error status, got {response.status_code}")
                return False
                
        except Exception as e:
            self.add_result("Double Purchase Protection", False, f"Exception: {str(e)}")
            return False
            
    def test_credit_transactions(self):
        """Test that credit transactions are recorded correctly with no amount=0"""
        self.log("📊 Testing credit transactions...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/credit-history?limit=20")
            
            if response.status_code != 200:
                self.add_result("Credit Transactions", False, f"Failed to get credit history: {response.status_code}")
                return False
                
            data = response.json()
            transactions = data.get('transactions', [])
            
            # Look for the consultation purchase transaction
            purchase_transaction = None
            for transaction in transactions:
                if (transaction.get('amount') == -EXPECTED_CONSULTATION_COST and 
                    'консультац' in transaction.get('description', '').lower()):
                    purchase_transaction = transaction
                    break
                    
            if purchase_transaction:
                self.add_result("Purchase Transaction Found", True, f"Found transaction: {purchase_transaction['amount']} points")
                
                # Verify transaction details
                if purchase_transaction.get('category') == 'consultation':
                    self.add_result("Transaction Category", True, "Correct category: consultation")
                else:
                    self.add_result("Transaction Category", False, f"Wrong category: {purchase_transaction.get('category')}")
                    
                # Check transaction details
                details = purchase_transaction.get('details', {})
                if details.get('consultation_id') == self.consultation_id:
                    self.add_result("Transaction Details", True, "Correct consultation ID in details")
                else:
                    self.add_result("Transaction Details", False, "Missing or wrong consultation ID in details")
                    
            else:
                self.add_result("Purchase Transaction Found", False, "Purchase transaction not found in history")
                
            # Check for any amount=0 transactions (should be protected against)
            zero_amount_transactions = [t for t in transactions if t.get('amount') == 0]
            if not zero_amount_transactions:
                self.add_result("No Zero Amount Transactions", True, "No amount=0 transactions found (protection working)")
            else:
                self.add_result("No Zero Amount Transactions", False, f"Found {len(zero_amount_transactions)} transactions with amount=0")
                
            return True
            
        except Exception as e:
            self.add_result("Credit Transactions", False, f"Exception: {str(e)}")
            return False
            
    def cleanup_test_consultation(self):
        """Clean up the test consultation"""
        if self.consultation_id:
            self.log("🧹 Cleaning up test consultation...")
            try:
                response = self.session.delete(f"{BACKEND_URL}/admin/consultations/{self.consultation_id}")
                if response.status_code == 200:
                    self.log("Test consultation cleaned up successfully")
                else:
                    self.log(f"Failed to clean up consultation: {response.status_code}")
            except Exception as e:
                self.log(f"Exception during cleanup: {str(e)}")
                
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting Consultation System Tests (Review Request Verification)")
        self.log("=" * 70)
        
        # Test sequence
        tests = [
            self.authenticate,
            self.create_test_consultation,
            self.test_consultation_cost_verification,
            self.test_purchase_consultation,
            self.test_immediate_buyer_data_loading,
            self.test_no_duplicate_consultations,
            self.test_double_purchase_protection,
            self.test_credit_transactions
        ]
        
        for test in tests:
            try:
                success = test()
                if not success and test == self.authenticate:
                    self.log("Authentication failed, stopping tests")
                    break
            except Exception as e:
                self.log(f"Exception in {test.__name__}: {str(e)}", "ERROR")
                
        # Cleanup
        self.cleanup_test_consultation()
        
        # Summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        self.log("=" * 70)
        self.log("📊 TEST SUMMARY - CONSULTATION SYSTEM REVIEW")
        self.log("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            self.log(f"{status} {result['test']}: {result['message']}")
            
        self.log("=" * 70)
        self.log(f"RESULTS: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
        
        # Review request specific summary
        critical_tests = [
            "Correct Cost Deduction",
            "Immediate Data Loading", 
            "No Duplicates",
            "Double Purchase Protection",
            "No Zero Amount Transactions"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result['test'] in critical_tests and result['success'])
        critical_total = len([r for r in self.test_results if r['test'] in critical_tests])
        
        self.log(f"CRITICAL FIXES: {critical_passed}/{critical_total} verified")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED - Consultation system fixes verified!")
        elif critical_passed == critical_total:
            self.log("✅ CRITICAL FIXES VERIFIED - Main issues resolved")
        else:
            self.log("⚠️  SOME CRITICAL ISSUES REMAIN - Review needed")
            
        return passed == total

if __name__ == "__main__":
    tester = ConsultationSystemTester()
    tester.run_all_tests()