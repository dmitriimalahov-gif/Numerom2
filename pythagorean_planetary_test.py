#!/usr/bin/env python3
"""
Pythagorean Square and Planetary Energy Integration Test Suite

Review Request: Протестировать интегрированную функциональность Квадрата Пифагора с планетарными энергиями

Test Requirements:
1. POST /api/numerology/pythagorean-square - должен возвращать корректную структуру квадрата
2. GET /api/charts/planetary-energy/7 - должен возвращать планетарные энергии для интеграции
3. Проверить что оба endpoint работают с аутентификацией
4. Убедиться что структура данных соответствует ожиданиям frontend кода
5. Проверить корректность соответствия планет между квадратом и энергиями:
   - Позиция 1 (Surya) = surya в энергиях
   - Позиция 2 (Chandra) = chandra в энергиях  
   - Позиция 3 (Guru) = guru в энергиях
   - И так далее для всех 9 позиций

Использовать существующие тестовые креды dmitrii.malahov@gmail.com / 756bvy67H
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"
TEST_BIRTH_DATE = "15.03.1990"  # Test birth date for calculations

class PythagoreanPlanetaryTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.pythagorean_data = None
        self.planetary_data = None
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate with test credentials"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                user_info = data.get('user', {})
                self.log_test("Authentication", True, 
                    f"Logged in as {user_info.get('email')} with {user_info.get('credits_remaining', 0)} credits")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_pythagorean_square_endpoint(self):
        """Test POST /api/numerology/pythagorean-square endpoint"""
        try:
            response = self.session.post(f"{BACKEND_URL}/numerology/pythagorean-square", 
                                       json={"birth_date": TEST_BIRTH_DATE})
            
            if response.status_code == 200:
                self.pythagorean_data = response.json()
                
                # Check required fields in response
                required_fields = ['square', 'horizontal_sums', 'vertical_sums', 'diagonal_sums', 'additional_numbers']
                missing_fields = [field for field in required_fields if field not in self.pythagorean_data]
                
                if missing_fields:
                    self.log_test("Pythagorean Square Structure", False, 
                        f"Missing required fields: {missing_fields}")
                    return False
                
                # Check square matrix structure (should be 3x3)
                square = self.pythagorean_data.get('square', [])
                if len(square) != 3 or any(len(row) != 3 for row in square):
                    self.log_test("Pythagorean Square Matrix", False, 
                        f"Square matrix is not 3x3: {square}")
                    return False
                
                # Check additional numbers (should be 4 numbers)
                additional_numbers = self.pythagorean_data.get('additional_numbers', [])
                if len(additional_numbers) != 4:
                    self.log_test("Pythagorean Additional Numbers", False, 
                        f"Expected 4 additional numbers, got {len(additional_numbers)}: {additional_numbers}")
                    return False
                
                # Check if number_positions exists for planetary mapping
                if 'number_positions' not in self.pythagorean_data:
                    self.log_test("Pythagorean Planetary Positions", False, 
                        "Missing number_positions field for planetary mapping")
                    return False
                
                self.log_test("Pythagorean Square Endpoint", True, 
                    f"Valid structure with 3x3 matrix, 4 additional numbers: {additional_numbers}")
                return True
                
            else:
                self.log_test("Pythagorean Square Endpoint", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Pythagorean Square Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_planetary_energy_endpoint(self):
        """Test GET /api/charts/planetary-energy/7 endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/charts/planetary-energy/7")
            
            if response.status_code == 200:
                self.planetary_data = response.json()
                
                # Check required fields
                required_fields = ['chart_data', 'period', 'user_birth_date']
                missing_fields = [field for field in required_fields if field not in self.planetary_data]
                
                if missing_fields:
                    self.log_test("Planetary Energy Structure", False, 
                        f"Missing required fields: {missing_fields}")
                    return False
                
                # Check chart_data structure
                chart_data = self.planetary_data.get('chart_data', [])
                if not chart_data or len(chart_data) != 7:
                    self.log_test("Planetary Energy Chart Data", False, 
                        f"Expected 7 days of data, got {len(chart_data)}")
                    return False
                
                # Check planetary energies in first day
                first_day = chart_data[0] if chart_data else {}
                expected_planets = ['surya', 'chandra', 'mangal', 'budha', 'guru', 'shukra', 'shani', 'rahu', 'ketu']
                
                missing_planets = []
                for planet in expected_planets:
                    if planet not in first_day:
                        missing_planets.append(planet)
                
                if missing_planets:
                    self.log_test("Planetary Energy Planets", False, 
                        f"Missing planets in energy data: {missing_planets}")
                    return False
                
                self.log_test("Planetary Energy Endpoint", True, 
                    f"Valid structure with 7 days, all 9 planets present")
                return True
                
            else:
                self.log_test("Planetary Energy Endpoint", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Planetary Energy Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_planetary_correspondence(self):
        """Test correspondence between Pythagorean Square positions and Planetary Energies"""
        if not self.pythagorean_data or not self.planetary_data:
            self.log_test("Planetary Correspondence", False, 
                "Missing Pythagorean or Planetary data for comparison")
            return False
        
        try:
            # Expected mapping between Pythagorean positions and planetary energies
            expected_mapping = {
                1: 'surya',    # Position 1 (Surya/Sun)
                2: 'chandra',  # Position 2 (Chandra/Moon)
                3: 'guru',     # Position 3 (Guru/Jupiter)
                4: 'rahu',     # Position 4 (Rahu)
                5: 'budha',    # Position 5 (Budha/Mercury)
                6: 'shukra',   # Position 6 (Shukra/Venus)
                7: 'ketu',     # Position 7 (Ketu)
                8: 'shani',    # Position 8 (Shani/Saturn)
                9: 'mangal'    # Position 9 (Mangal/Mars)
            }
            
            # Get number positions from Pythagorean data
            number_positions = self.pythagorean_data.get('number_positions', {})
            
            # Get first day planetary energies
            chart_data = self.planetary_data.get('chart_data', [])
            if not chart_data:
                self.log_test("Planetary Correspondence", False, "No chart data available")
                return False
            
            first_day_energies = chart_data[0]
            
            # Check correspondence
            correspondence_results = []
            for position, expected_planet in expected_mapping.items():
                # Check if position exists in Pythagorean square
                position_exists = str(position) in number_positions
                
                # Check if planet exists in energies
                planet_exists = expected_planet in first_day_energies
                
                if position_exists and planet_exists:
                    correspondence_results.append(f"✅ Position {position} ({expected_planet}) - Both present")
                elif not position_exists:
                    correspondence_results.append(f"❌ Position {position} missing in Pythagorean data")
                elif not planet_exists:
                    correspondence_results.append(f"❌ Planet {expected_planet} missing in energy data")
            
            # Count successful correspondences
            successful_correspondences = len([r for r in correspondence_results if r.startswith('✅')])
            total_correspondences = len(expected_mapping)
            
            success = successful_correspondences == total_correspondences
            details = f"Successful correspondences: {successful_correspondences}/{total_correspondences}\n" + \
                     "\n".join(correspondence_results)
            
            self.log_test("Planetary Correspondence", success, details)
            return success
            
        except Exception as e:
            self.log_test("Planetary Correspondence", False, f"Exception: {str(e)}")
            return False
    
    def test_data_structure_compatibility(self):
        """Test that data structures are compatible with frontend expectations"""
        try:
            compatibility_issues = []
            
            # Check Pythagorean data structure
            if self.pythagorean_data:
                # Check square matrix format
                square = self.pythagorean_data.get('square', [])
                for i, row in enumerate(square):
                    for j, cell in enumerate(row):
                        if not isinstance(cell, (int, list)):
                            compatibility_issues.append(f"Square cell [{i}][{j}] has invalid type: {type(cell)}")
                
                # Check additional numbers are integers
                additional_numbers = self.pythagorean_data.get('additional_numbers', [])
                for i, num in enumerate(additional_numbers):
                    if not isinstance(num, int):
                        compatibility_issues.append(f"Additional number {i} is not integer: {type(num)}")
                
                # Check sums are integers
                for sum_type in ['horizontal_sums', 'vertical_sums', 'diagonal_sums']:
                    sums = self.pythagorean_data.get(sum_type, [])
                    for i, sum_val in enumerate(sums):
                        if not isinstance(sum_val, int):
                            compatibility_issues.append(f"{sum_type}[{i}] is not integer: {type(sum_val)}")
            
            # Check Planetary data structure
            if self.planetary_data:
                chart_data = self.planetary_data.get('chart_data', [])
                for day_idx, day_data in enumerate(chart_data):
                    # Check required fields for each day
                    required_day_fields = ['date', 'day_name']
                    for field in required_day_fields:
                        if field not in day_data:
                            compatibility_issues.append(f"Day {day_idx} missing field: {field}")
                    
                    # Check planetary energy values are numeric
                    expected_planets = ['surya', 'chandra', 'mangal', 'budha', 'guru', 'shukra', 'shani', 'rahu', 'ketu']
                    for planet in expected_planets:
                        if planet in day_data:
                            energy_value = day_data[planet]
                            if not isinstance(energy_value, (int, float)):
                                compatibility_issues.append(f"Day {day_idx} planet {planet} has non-numeric energy: {type(energy_value)}")
                            elif not (0 <= energy_value <= 100):
                                compatibility_issues.append(f"Day {day_idx} planet {planet} energy out of range 0-100: {energy_value}")
            
            success = len(compatibility_issues) == 0
            details = "All data structures compatible with frontend" if success else \
                     f"Compatibility issues found:\n" + "\n".join(compatibility_issues)
            
            self.log_test("Data Structure Compatibility", success, details)
            return success
            
        except Exception as e:
            self.log_test("Data Structure Compatibility", False, f"Exception: {str(e)}")
            return False
    
    def test_authentication_requirements(self):
        """Test that both endpoints require authentication"""
        try:
            # Create session without auth token
            unauth_session = requests.Session()
            
            # Test Pythagorean endpoint without auth
            response1 = unauth_session.post(f"{BACKEND_URL}/numerology/pythagorean-square", 
                                          json={"birth_date": TEST_BIRTH_DATE})
            
            # Test Planetary endpoint without auth
            response2 = unauth_session.get(f"{BACKEND_URL}/charts/planetary-energy/7")
            
            # Both should return 401 Unauthorized
            pythagorean_auth_required = response1.status_code == 401
            planetary_auth_required = response2.status_code == 401
            
            success = pythagorean_auth_required and planetary_auth_required
            details = f"Pythagorean auth required: {pythagorean_auth_required} (status: {response1.status_code}), " + \
                     f"Planetary auth required: {planetary_auth_required} (status: {response2.status_code})"
            
            self.log_test("Authentication Requirements", success, details)
            return success
            
        except Exception as e:
            self.log_test("Authentication Requirements", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Starting Pythagorean Square and Planetary Energy Integration Tests")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("\n❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Step 2: Test individual endpoints
        pythagorean_success = self.test_pythagorean_square_endpoint()
        planetary_success = self.test_planetary_energy_endpoint()
        
        # Step 3: Test authentication requirements
        auth_success = self.test_authentication_requirements()
        
        # Step 4: Test integration aspects
        correspondence_success = self.test_planetary_correspondence()
        compatibility_success = self.test_data_structure_compatibility()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status}: {result['test']}")
        
        print(f"\n🎯 Overall Success Rate: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
        
        # Determine overall success
        critical_tests = [pythagorean_success, planetary_success, correspondence_success]
        overall_success = all(critical_tests)
        
        if overall_success:
            print("🎉 INTEGRATION TEST SUITE PASSED: Pythagorean Square and Planetary Energy integration working correctly!")
        else:
            print("⚠️  INTEGRATION TEST SUITE FAILED: Issues found in Pythagorean-Planetary integration")
        
        return overall_success

def main():
    """Main test execution"""
    test_suite = PythagoreanPlanetaryTestSuite()
    success = test_suite.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()