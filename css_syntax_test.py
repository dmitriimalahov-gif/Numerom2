#!/usr/bin/env python3
"""
CSS Syntax Testing Suite for NUMEROM HTML Reports
Focused testing of CSS syntax fixes in HTML report generation as requested in review.
"""

import requests
import json
import re
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class CSSValidationTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.test_results = []
        
        # Super admin credentials as specified in review request
        self.admin_credentials = {
            "email": "dmitrii.malahov@gmail.com",
            "password": "756bvy67H"
        }
        
    def log_result(self, test_name, success, message="", details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def make_request(self, method, endpoint, data=None, headers=None, timeout=30):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if headers:
            default_headers.update(headers)
            
        if self.auth_token:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=timeout)
            elif method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=timeout)
            else:
                return None, f"Unsupported method: {method}"
                
            return response, None
        except requests.exceptions.Timeout:
            return None, f"Request timeout after {timeout}s"
        except requests.exceptions.RequestException as e:
            return None, f"Request error: {str(e)}"
    
    def authenticate_super_admin(self):
        """Authenticate with super admin credentials"""
        print("🔐 Authenticating Super Admin...")
        
        response, error = self.make_request("POST", "/auth/login", self.admin_credentials)
        
        if error:
            self.log_result("Super Admin Authentication", False, f"Request failed: {error}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            user_info = data.get("user", {})
            
            # Verify super admin status
            if user_info.get("is_super_admin"):
                self.log_result("Super Admin Authentication", True, 
                              f"Authenticated as {user_info.get('email')} with {user_info.get('credits_remaining', 0)} credits")
                return True
            else:
                self.log_result("Super Admin Authentication", False, "User is not super admin")
                return False
        else:
            self.log_result("Super Admin Authentication", False, 
                          f"Login failed: {response.status_code} - {response.text}")
            return False
    
    def extract_css_from_html(self, html_content):
        """Extract all CSS content from HTML"""
        css_blocks = []
        
        # Extract inline CSS from <style> tags
        style_pattern = r'<style[^>]*>(.*?)</style>'
        style_matches = re.findall(style_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in style_matches:
            css_blocks.append(("inline", match))
        
        # Extract CSS from style attributes
        style_attr_pattern = r'style\s*=\s*["\']([^"\']*)["\']'
        style_attr_matches = re.findall(style_attr_pattern, html_content, re.IGNORECASE)
        
        for match in style_attr_matches:
            css_blocks.append(("attribute", match))
        
        return css_blocks
    
    def validate_css_syntax(self, css_content, css_type="inline"):
        """Comprehensive CSS syntax validation"""
        errors = []
        warnings = []
        
        # Remove comments first
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # 1. Check for balanced braces
        open_braces = css_content.count('{')
        close_braces = css_content.count('}')
        if open_braces != close_braces:
            errors.append(f"Mismatched braces: {open_braces} open, {close_braces} close")
        
        # 2. Check for unclosed strings
        single_quotes = css_content.count("'") - css_content.count("\\'")
        double_quotes = css_content.count('"') - css_content.count('\\"')
        if single_quotes % 2 != 0:
            errors.append("Unclosed single quote string")
        if double_quotes % 2 != 0:
            errors.append("Unclosed double quote string")
        
        # 3. Check for missing semicolons in property declarations
        if css_type == "inline":
            # Split by rules (between braces)
            rules = re.split(r'[{}]', css_content)
            for i, rule in enumerate(rules):
                if i % 2 == 1:  # This is a rule body (between braces)
                    rule = rule.strip()
                    if rule:
                        # Split by semicolons to get individual properties
                        properties = [prop.strip() for prop in rule.split(';') if prop.strip()]
                        for prop in properties:
                            if ':' in prop and not prop.endswith(';') and prop != properties[-1]:
                                # Last property in a rule doesn't need semicolon
                                warnings.append(f"Missing semicolon after property: '{prop}'")
        
        # 4. Check for invalid property syntax
        property_pattern = r'([a-zA-Z-]+)\s*:\s*([^;{}]+)'
        properties = re.findall(property_pattern, css_content)
        
        for prop_name, prop_value in properties:
            prop_name = prop_name.strip()
            prop_value = prop_value.strip()
            
            # Check for empty values
            if not prop_value:
                errors.append(f"Empty value for property '{prop_name}'")
            
            # Check for invalid property names (basic validation)
            if not re.match(r'^[a-zA-Z-]+$', prop_name):
                errors.append(f"Invalid property name: '{prop_name}'")
            
            # Check for common value syntax errors
            if prop_name in ['color', 'background-color', 'border-color']:
                # Color values should be valid
                if not re.match(r'^(#[0-9a-fA-F]{3,6}|rgb\(|rgba\(|hsl\(|[a-zA-Z]+).*', prop_value):
                    warnings.append(f"Potentially invalid color value for '{prop_name}': '{prop_value}'")
        
        # 5. Check for duplicate properties in same rule
        if css_type == "inline":
            rules = re.split(r'[{}]', css_content)
            for i, rule in enumerate(rules):
                if i % 2 == 1:  # Rule body
                    properties = re.findall(r'([a-zA-Z-]+)\s*:', rule)
                    prop_counts = {}
                    for prop in properties:
                        prop_counts[prop] = prop_counts.get(prop, 0) + 1
                    
                    for prop, count in prop_counts.items():
                        if count > 1:
                            warnings.append(f"Duplicate property '{prop}' in same rule ({count} times)")
        
        return errors, warnings
    
    def test_css_syntax_light_theme(self):
        """Test CSS syntax in light theme HTML report"""
        print("\n🌞 Testing CSS Syntax - Light Theme...")
        
        test_data = {
            "theme": "light",
            "selected_calculations": ["personal_numbers", "pythagorean_square", "vedic_numerology"]
        }
        
        response, error = self.make_request("POST", "/reports/html/numerology", test_data)
        
        if error:
            self.log_result("CSS Syntax Light Theme", False, f"Request failed: {error}")
            return False
        
        if response.status_code != 200:
            self.log_result("CSS Syntax Light Theme", False, 
                          f"HTTP error: {response.status_code} - {response.text}")
            return False
        
        html_content = response.text
        css_blocks = self.extract_css_from_html(html_content)
        
        total_errors = 0
        total_warnings = 0
        
        for css_type, css_content in css_blocks:
            errors, warnings = self.validate_css_syntax(css_content, css_type)
            total_errors += len(errors)
            total_warnings += len(warnings)
            
            if errors:
                self.log_result("CSS Syntax Light Theme", False, 
                              f"CSS errors in {css_type}: {errors}")
                return False
        
        self.log_result("CSS Syntax Light Theme", True, 
                      f"Valid CSS syntax - {len(css_blocks)} blocks, {total_warnings} warnings")
        return True
    
    def test_css_syntax_dark_theme(self):
        """Test CSS syntax in dark theme HTML report"""
        print("\n🌙 Testing CSS Syntax - Dark Theme...")
        
        test_data = {
            "theme": "dark",
            "selected_calculations": ["personal_numbers", "pythagorean_square", "vedic_numerology"]
        }
        
        response, error = self.make_request("POST", "/reports/html/numerology", test_data)
        
        if error:
            self.log_result("CSS Syntax Dark Theme", False, f"Request failed: {error}")
            return False
        
        if response.status_code != 200:
            self.log_result("CSS Syntax Dark Theme", False, 
                          f"HTTP error: {response.status_code} - {response.text}")
            return False
        
        html_content = response.text
        css_blocks = self.extract_css_from_html(html_content)
        
        total_errors = 0
        total_warnings = 0
        
        for css_type, css_content in css_blocks:
            errors, warnings = self.validate_css_syntax(css_content, css_type)
            total_errors += len(errors)
            total_warnings += len(warnings)
            
            if errors:
                self.log_result("CSS Syntax Dark Theme", False, 
                              f"CSS errors in {css_type}: {errors}")
                return False
        
        self.log_result("CSS Syntax Dark Theme", True, 
                      f"Valid CSS syntax - {len(css_blocks)} blocks, {total_warnings} warnings")
        return True
    
    def test_css_properties_completeness(self):
        """Test that CSS includes all necessary styling properties"""
        print("\n🎨 Testing CSS Properties Completeness...")
        
        test_data = {
            "theme": "light",
            "selected_calculations": ["personal_numbers", "pythagorean_square"]
        }
        
        response, error = self.make_request("POST", "/reports/html/numerology", test_data)
        
        if error:
            self.log_result("CSS Properties Completeness", False, f"Request failed: {error}")
            return False
        
        if response.status_code != 200:
            self.log_result("CSS Properties Completeness", False, 
                          f"HTTP error: {response.status_code}")
            return False
        
        html_content = response.text
        
        # Check for essential CSS properties
        essential_properties = [
            'color:', 'background-color:', 'font-family:', 'font-size:',
            'margin:', 'padding:', 'border:', 'width:', 'height:',
            'display:', 'text-align:', 'line-height:'
        ]
        
        found_properties = []
        missing_properties = []
        
        for prop in essential_properties:
            if prop in html_content.lower():
                found_properties.append(prop)
            else:
                missing_properties.append(prop)
        
        # We should have at least 80% of essential properties
        coverage = len(found_properties) / len(essential_properties)
        
        if coverage < 0.8:
            self.log_result("CSS Properties Completeness", False, 
                          f"Insufficient CSS coverage: {coverage:.1%}, missing: {missing_properties}")
            return False
        
        self.log_result("CSS Properties Completeness", True, 
                      f"Good CSS coverage: {coverage:.1%}, found {len(found_properties)} properties")
        return True
    
    def test_html_content_type_and_structure(self):
        """Test HTML response content-type and basic structure"""
        print("\n📄 Testing HTML Content-Type and Structure...")
        
        test_data = {
            "theme": "light",
            "selected_calculations": ["personal_numbers"]
        }
        
        response, error = self.make_request("POST", "/reports/html/numerology", test_data)
        
        if error:
            self.log_result("HTML Content-Type Structure", False, f"Request failed: {error}")
            return False
        
        if response.status_code != 200:
            self.log_result("HTML Content-Type Structure", False, 
                          f"HTTP error: {response.status_code}")
            return False
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'text/html' not in content_type:
            self.log_result("HTML Content-Type Structure", False, 
                          f"Wrong content-type: {content_type}")
            return False
        
        html_content = response.text
        
        # Check basic HTML structure
        structure_checks = [
            ('DOCTYPE', html_content.strip().startswith('<!DOCTYPE')),
            ('HTML tag', '<html' in html_content.lower()),
            ('HEAD section', '<head>' in html_content.lower()),
            ('BODY section', '<body>' in html_content.lower()),
            ('NUMEROM branding', 'NUMEROM' in html_content),
            ('CSS styles', '<style' in html_content.lower() or 'stylesheet' in html_content.lower())
        ]
        
        failed_checks = [check[0] for check in structure_checks if not check[1]]
        
        if failed_checks:
            self.log_result("HTML Content-Type Structure", False, 
                          f"Failed structure checks: {failed_checks}")
            return False
        
        self.log_result("HTML Content-Type Structure", True, 
                      f"Valid HTML structure with correct content-type: {content_type}")
        return True
    
    def test_various_calculation_combinations(self):
        """Test CSS syntax with various calculation combinations"""
        print("\n🧮 Testing CSS Syntax with Various Calculations...")
        
        calculation_sets = [
            ["personal_numbers"],
            ["pythagorean_square"],
            ["vedic_numerology"],
            ["personal_numbers", "pythagorean_square"],
            ["personal_numbers", "vedic_numerology"],
            ["pythagorean_square", "vedic_numerology"],
            ["personal_numbers", "pythagorean_square", "vedic_numerology"]
        ]
        
        all_passed = True
        
        for i, calculations in enumerate(calculation_sets):
            test_data = {
                "theme": "light",
                "selected_calculations": calculations
            }
            
            response, error = self.make_request("POST", "/reports/html/numerology", test_data)
            
            if error:
                self.log_result(f"CSS Syntax Calculations {i+1}", False, f"Request failed: {error}")
                all_passed = False
                continue
            
            if response.status_code != 200:
                self.log_result(f"CSS Syntax Calculations {i+1}", False, 
                              f"HTTP error: {response.status_code}")
                all_passed = False
                continue
            
            html_content = response.text
            css_blocks = self.extract_css_from_html(html_content)
            
            has_errors = False
            for css_type, css_content in css_blocks:
                errors, warnings = self.validate_css_syntax(css_content, css_type)
                if errors:
                    self.log_result(f"CSS Syntax Calculations {i+1}", False, 
                                  f"CSS errors with {calculations}: {errors}")
                    has_errors = True
                    all_passed = False
                    break
            
            if not has_errors:
                self.log_result(f"CSS Syntax Calculations {i+1}", True, 
                              f"Valid CSS with calculations: {calculations}")
        
        return all_passed
    
    def run_all_tests(self):
        """Run all CSS syntax validation tests"""
        print("🎯 Starting CSS Syntax Validation Testing Suite")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate_super_admin():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all tests
        tests = [
            self.test_css_syntax_light_theme,
            self.test_css_syntax_dark_theme,
            self.test_css_properties_completeness,
            self.test_html_content_type_and_structure,
            self.test_various_calculation_combinations
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 CSS Syntax Testing Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All CSS syntax tests passed! CSS fixes are working correctly.")
            print("✅ HTML reports are generated without CSS syntax errors.")
        else:
            print(f"⚠️  {total - passed} tests failed. CSS syntax issues detected.")
        
        return passed == total

if __name__ == "__main__":
    tester = CSSValidationTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)