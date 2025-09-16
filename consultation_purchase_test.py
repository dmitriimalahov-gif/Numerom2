#!/usr/bin/env python3
"""
Consultation Purchase System Test - Review Request Testing
Testing the fixed consultation and points system as specified in review request.

CRITICAL BUGS FIXED (according to review):
1. ✅ Removed duplicate consultations in admin panel
2. ✅ Fixed user data loading delay - now loads immediately after purchase
3. ✅ Cleaned duplicate credit transactions
4. ✅ Fixed incorrect point allocation - added protection against amount=0 transactions
5. ✅ Set fixed cost for personal consultations - 6667 points
6. ✅ Added protection against double purchases (30-second cooldown)
7. ✅ Fixed user balances

TESTING SCENARIO:
1. Login as dmitrii.malahov@gmail.com (expected balance: 10000 points)
2. Find available consultation and buy it for 6667 points
3. Check remaining balance is 3333 points
4. Check admin panel shows buyer data IMMEDIATELY
5. Check no duplicate records
6. Test double purchase protection

Credentials: dmitrii.malahov@gmail.com / 756bvy67H
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"
EXPECTED_CONSULTATION_COST = 6667
EXPECTED_INITIAL_BALANCE = 10000
EXPECTED_FINAL_BALANCE = 3333

class ConsultationPurchaseTester:
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
            
            # Check if balance matches expected
            if self.initial_balance == EXPECTED_INITIAL_BALANCE:
                self.add_result("Initial Balance Check", True, f"Balance is correct: {self.initial_balance} points")
            else:
                self.add_result("Initial Balance Check", False, f"Expected {EXPECTED_INITIAL_BALANCE}, got {self.initial_balance}")
            
            return True
            
        except Exception as e:
            self.add_result("Authentication", False, f"Exception during login: {str(e)}")
            return False
            
    def test_get_available_consultations(self):
        """Test GET /api/user/consultations - get available consultations"""
        self.log("📋 Testing available consultations retrieval...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/consultations")
            
            if response.status_code != 200:
                self.add_result("Get Consultations", False, f"Failed to get consultations: {response.status_code} - {response.text}")
                return False
                
            consultations = response.json()
            
            if not consultations:
                self.add_result("Get Consultations", False, "No consultations available for purchase")
                return False
                
            # Find a consultation to purchase
            available_consultation = None
            for consultation in consultations:
                if consultation.get('is_active', False) and not consultation.get('purchased_by_user', False):
                    available_consultation = consultation
                    break
                    
            if not available_consultation:
                self.add_result("Get Consultations", False, "No available consultations found for purchase")
                return False
                
            self.consultation_id = available_consultation['id']
            consultation_cost = available_consultation.get('cost_credits', 0)
            
            self.log(f"Found consultation: {available_consultation.get('title', 'Untitled')}")
            self.log(f"Consultation ID: {self.consultation_id}")
            self.log(f"Cost: {consultation_cost} credits")
            
            # Check if cost matches expected
            if consultation_cost == EXPECTED_CONSULTATION_COST:
                self.add_result("Consultation Cost Check", True, f"Cost is correct: {consultation_cost} points")
            else:
                self.add_result("Consultation Cost Check", False, f"Expected {EXPECTED_CONSULTATION_COST}, got {consultation_cost}")
                
            self.add_result("Get Consultations", True, f"Found {len(consultations)} consultations, selected ID: {self.consultation_id}")
            return True
            
        except Exception as e:
            self.add_result("Get Consultations", False, f"Exception: {str(e)}")
            return False
            
    def test_purchase_consultation(self):
        """Test POST /api/user/consultations/{id}/purchase - purchase consultation"""
        if not self.consultation_id:
            self.add_result("Purchase Consultation", False, "No consultation ID available for purchase")
            return False
            
        self.log("💳 Testing consultation purchase...")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/user/consultations/{self.consultation_id}/purchase")
            
            if response.status_code != 200:
                self.add_result("Purchase Consultation", False, f"Purchase failed: {response.status_code} - {response.text}")
                return False
                
            result = response.json()
            
            self.log(f"Purchase result: {result}")
            
            # Check if purchase was successful
            if result.get('success', False):
                self.add_result("Purchase Consultation", True, f"Purchase successful: {result.get('message', 'No message')}")
                return True
            else:
                self.add_result("Purchase Consultation", False, f"Purchase failed: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.add_result("Purchase Consultation", False, f"Exception during purchase: {str(e)}")
            return False
            
    def test_balance_after_purchase(self):
        """Test that balance is correctly updated after purchase"""
        self.log("💰 Testing balance after purchase...")
        
        try:
            # Get current user data to check balance
            response = self.session.get(f"{BACKEND_URL}/auth/me")
            
            if response.status_code != 200:
                self.add_result("Balance Check", False, f"Failed to get user data: {response.status_code}")
                return False
                
            user_data = response.json()
            current_balance = user_data.get('credits_remaining', 0)
            
            self.log(f"Current balance: {current_balance}")
            self.log(f"Expected balance: {EXPECTED_FINAL_BALANCE}")
            
            if current_balance == EXPECTED_FINAL_BALANCE:
                self.add_result("Balance After Purchase", True, f"Balance correctly updated: {current_balance} points")
                return True
            else:
                self.add_result("Balance After Purchase", False, f"Expected {EXPECTED_FINAL_BALANCE}, got {current_balance}")
                return False
                
        except Exception as e:
            self.add_result("Balance Check", False, f"Exception: {str(e)}")
            return False
            
    def test_admin_consultations_with_buyer_data(self):
        """Test GET /api/admin/consultations - check buyer data loads immediately"""
        self.log("👨‍💼 Testing admin consultations with buyer data...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/consultations")
            
            if response.status_code != 200:
                self.add_result("Admin Consultations", False, f"Failed to get admin consultations: {response.status_code} - {response.text}")
                return False
                
            consultations = response.json()
            
            # Find our purchased consultation
            purchased_consultation = None
            for consultation in consultations:
                if consultation.get('id') == self.consultation_id:
                    purchased_consultation = consultation
                    break
                    
            if not purchased_consultation:
                self.add_result("Admin Consultations", False, f"Purchased consultation {self.consultation_id} not found in admin list")
                return False
                
            # Check if buyer data is present
            buyer_data = purchased_consultation.get('buyer_data')
            if buyer_data:
                buyer_email = buyer_data.get('email')
                if buyer_email == TEST_EMAIL:
                    self.add_result("Buyer Data Loading", True, f"Buyer data loaded immediately: {buyer_email}")
                else:
                    self.add_result("Buyer Data Loading", False, f"Wrong buyer email: expected {TEST_EMAIL}, got {buyer_email}")
            else:
                self.add_result("Buyer Data Loading", False, "Buyer data not found in consultation")
                
            # Check for duplicates
            consultation_count = sum(1 for c in consultations if c.get('id') == self.consultation_id)
            if consultation_count == 1:
                self.add_result("No Duplicates", True, "No duplicate consultations found")
            else:
                self.add_result("No Duplicates", False, f"Found {consultation_count} instances of consultation {self.consultation_id}")
                
            return True
            
        except Exception as e:
            self.add_result("Admin Consultations", False, f"Exception: {str(e)}")
            return False
            
    def test_double_purchase_protection(self):
        """Test protection against double purchases (30-second cooldown)"""
        self.log("🛡️ Testing double purchase protection...")
        
        if not self.consultation_id:
            self.add_result("Double Purchase Protection", False, "No consultation ID for testing")
            return False
            
        try:
            # Attempt to purchase the same consultation again
            response = self.session.post(f"{BACKEND_URL}/user/consultations/{self.consultation_id}/purchase")
            
            # Should fail with appropriate error
            if response.status_code == 400 or response.status_code == 409:
                result = response.json()
                error_message = result.get('detail', result.get('message', 'Unknown error'))
                
                # Check if error mentions cooldown or already purchased
                if 'cooldown' in error_message.lower() or 'already' in error_message.lower() or 'purchased' in error_message.lower():
                    self.add_result("Double Purchase Protection", True, f"Protection working: {error_message}")
                    return True
                else:
                    self.add_result("Double Purchase Protection", False, f"Wrong error message: {error_message}")
                    return False
            else:
                self.add_result("Double Purchase Protection", False, f"Expected 400/409 error, got {response.status_code}")
                return False
                
        except Exception as e:
            self.add_result("Double Purchase Protection", False, f"Exception: {str(e)}")
            return False
            
    def test_credit_transactions(self):
        """Test that credit transactions are recorded correctly"""
        self.log("📊 Testing credit transactions...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/credit-history?limit=10")
            
            if response.status_code != 200:
                self.add_result("Credit Transactions", False, f"Failed to get credit history: {response.status_code}")
                return False
                
            data = response.json()
            transactions = data.get('transactions', [])
            
            # Look for the consultation purchase transaction
            purchase_transaction = None
            for transaction in transactions:
                if (transaction.get('amount') == -EXPECTED_CONSULTATION_COST and 
                    'consultation' in transaction.get('description', '').lower()):
                    purchase_transaction = transaction
                    break
                    
            if purchase_transaction:
                # Check that amount is not 0 (protection against amount=0 transactions)
                if purchase_transaction['amount'] != 0:
                    self.add_result("Credit Transactions", True, f"Transaction recorded correctly: {purchase_transaction['amount']} points")
                else:
                    self.add_result("Credit Transactions", False, "Found transaction with amount=0 (should be protected)")
            else:
                self.add_result("Credit Transactions", False, f"Purchase transaction not found in history")
                
            # Check for duplicate transactions
            consultation_transactions = [t for t in transactions if 'consultation' in t.get('description', '').lower()]
            if len(consultation_transactions) <= 1:
                self.add_result("No Duplicate Transactions", True, "No duplicate credit transactions found")
            else:
                self.add_result("No Duplicate Transactions", False, f"Found {len(consultation_transactions)} consultation transactions")
                
            return True
            
        except Exception as e:
            self.add_result("Credit Transactions", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting Consultation Purchase System Tests")
        self.log("=" * 60)
        
        # Test sequence
        tests = [
            self.authenticate,
            self.test_get_available_consultations,
            self.test_purchase_consultation,
            self.test_balance_after_purchase,
            self.test_admin_consultations_with_buyer_data,
            self.test_double_purchase_protection,
            self.test_credit_transactions
        ]
        
        for test in tests:
            try:
                success = test()
                if not success:
                    self.log(f"Test {test.__name__} failed, continuing with remaining tests...")
            except Exception as e:
                self.log(f"Exception in {test.__name__}: {str(e)}", "ERROR")
                
        # Summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        self.log("=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            self.log(f"{status} {result['test']}: {result['message']}")
            
        self.log("=" * 60)
        self.log(f"RESULTS: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED - Consultation purchase system working correctly!")
        else:
            self.log("⚠️  SOME TESTS FAILED - Issues found in consultation purchase system")
            
        return passed == total

if __name__ == "__main__":
    tester = ConsultationPurchaseTester()
    tester.run_all_tests()