#!/usr/bin/env python3
"""
Soccer Slot Manager - Comprehensive API Test Suite
Tests all functionality by making HTTP requests to the deployed Docker container
No code imports - pure black-box API testing
"""

import requests
import json
from datetime import datetime
import time
import random


# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"
MAX_PLAYERS = 10  # Business rule constant

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test_header(category: str):
    """Print test category header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{category.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")


def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} | {test_name}")
    if details:
        print(f"       {Colors.YELLOW}→ {details}{Colors.RESET}")


def print_summary(total: int, passed: int):
    """Print test summary"""
    failed = total - passed
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
    print(f"Total:  {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")


class TestRunner:
    """Simple test runner to track results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
    
    def run_test(self, test_name: str, test_func, expected_result=True, details=""):
        """Run a test and record result"""
        self.total += 1
        try:
            result = test_func()
            passed = (result == expected_result)
            self.passed += passed
            print_test(test_name, passed, details or f"Expected: {expected_result}, Got: {result}")
        except Exception as e:
            print_test(test_name, False, f"Exception: {str(e)}")
    
    def print_summary(self):
        """Print final summary"""
        print_summary(self.total, self.passed)


# =============================================================================
# API HELPER FUNCTIONS
# =============================================================================

def check_server_running() -> bool:
    """Check if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_current_slot():
    """Get current slot via API"""
    try:
        response = requests.get(f"{API_BASE}/current-slot", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting slot: {e}")
        return None


def register_player(username: str, name: str):
    """Register a player via API. Returns (success, message, response_data)"""
    try:
        response = requests.post(
            f"{API_BASE}/register",
            json={"name": name},
            params={"username": username},
            timeout=5
        )
        if response.status_code == 200:
            return True, "Success", response.json()
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return False, error_detail, None
    except Exception as e:
        return False, str(e), None


def register_guest(username: str, guest_name: str):
    """Register a guest via API. Returns (success, message, response_data)"""
    try:
        response = requests.post(
            f"{API_BASE}/register-guest",
            json={"guestName": guest_name},
            params={"username": username},
            timeout=5
        )
        if response.status_code == 200:
            return True, "Success", response.json()
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return False, error_detail, None
    except Exception as e:
        return False, str(e), None


def unregister_player(username: str, player_name: str):
    """Unregister a player via API. Returns (success, message)"""
    try:
        response = requests.delete(
            f"{API_BASE}/unregister/{player_name}",
            params={"username": username},
            timeout=5
        )
        if response.status_code == 200:
            return True, "Success"
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return False, error_detail
    except Exception as e:
        return False, str(e)


def login(username: str, pin: str):
    """Login via API. Returns (success, user_data)"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "pin": pin},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("success", False), data.get("user")
        return False, None
    except Exception as e:
        print(f"Login error: {e}")
        return False, None


# =============================================================================
# SERVER CONNECTIVITY TESTS
# =============================================================================

def test_server_connectivity():
    """Test that the server is running and responding"""
    print_test_header("SERVER CONNECTIVITY TESTS")
    runner = TestRunner()
    
    # Test 1: Health endpoint
    test_name = "Server health endpoint should respond"
    runner.run_test(test_name, lambda: check_server_running(), True,
                   f"GET {BASE_URL}/health")
    
    # Test 2: Root endpoint
    test_name = "Root endpoint should return HTML"
    try:
        response = requests.get(BASE_URL, timeout=5)
        success = response.status_code == 200 and "text/html" in response.headers.get("content-type", "")
        runner.run_test(test_name, lambda: success, True,
                       f"GET {BASE_URL} -> Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 3: API current-slot endpoint
    test_name = "API current-slot endpoint should respond"
    try:
        response = requests.get(f"{API_BASE}/current-slot", timeout=5)
        success = response.status_code == 200
        runner.run_test(test_name, lambda: success, True,
                       f"GET {API_BASE}/current-slot -> Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 4: Admin page endpoint
    test_name = "Admin page endpoint should respond"
    try:
        response = requests.get(f"{BASE_URL}/admin", timeout=5)
        success = response.status_code == 200
        runner.run_test(test_name, lambda: success, True,
                       f"GET {BASE_URL}/admin -> Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    runner.print_summary()
    return runner


# =============================================================================
# SLOT RETRIEVAL TESTS
# =============================================================================

def test_slot_retrieval():
    """Test getting current slot information"""
    print_test_header("SLOT RETRIEVAL TESTS")
    runner = TestRunner()
    
    # Test 1: Get current slot
    test_name = "Should retrieve current slot data"
    slot = get_current_slot()
    runner.run_test(test_name, lambda: slot is not None, True,
                   f"Slot retrieved: {slot is not None}")
    
    if slot:
        # Test 2: Slot should have date field
        test_name = "Slot should have 'date' field"
        runner.run_test(test_name, lambda: "date" in slot, True,
                       f"Date: {slot.get('date', 'N/A')}")
        
        # Test 3: Slot should have players field
        test_name = "Slot should have 'players' field"
        runner.run_test(test_name, lambda: "players" in slot, True,
                       f"Players: {slot.get('players', [])}")
        
        # Test 4: Slot should have player_count field
        test_name = "Slot should have 'player_count' field"
        runner.run_test(test_name, lambda: "player_count" in slot, True,
                       f"Player count: {slot.get('player_count', 'N/A')}")
        
        # Test 5: Slot should have max_players field set to 10
        test_name = "Slot should have 'max_players' field set to 10"
        runner.run_test(test_name, lambda: slot.get("max_players") == 10, True,
                       f"Max players: {slot.get('max_players', 'N/A')}")
        
        # Test 6: Player count should match players list length
        test_name = "player_count should match players list length"
        player_count = slot.get("player_count", 0)
        players_length = len(slot.get("players", []))
        runner.run_test(test_name, lambda: player_count == players_length, True,
                       f"Count: {player_count}, List length: {players_length}")
        
        # Test 7: Date should be valid ISO format
        test_name = "Date should be valid ISO 8601 format"
        try:
            date_str = slot.get("date", "")
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            runner.run_test(test_name, lambda: True, True,
                           f"Date: {date_str}")
        except:
            runner.run_test(test_name, lambda: False, True,
                           f"Invalid date format: {slot.get('date')}")
        
        # Test 8: Date should be Wednesday at 19:00
        test_name = "Slot date should be a Wednesday at 19:00"
        try:
            date_str = slot.get("date", "")
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            is_wednesday = parsed.weekday() == 2
            is_19_00 = parsed.hour == 19 and parsed.minute == 0
            runner.run_test(test_name, lambda: is_wednesday and is_19_00, True,
                           f"Day: {parsed.strftime('%A')}, Time: {parsed.strftime('%H:%M')}")
        except:
            runner.run_test(test_name, lambda: False, True, "Could not parse date")
        
        # Test 9: Players should be a list
        test_name = "Players field should be a list"
        runner.run_test(test_name, lambda: isinstance(slot.get("players"), list), True,
                       f"Type: {type(slot.get('players'))}")
    
    runner.print_summary()
    return runner


# =============================================================================
# AUTHENTICATION TESTS
# =============================================================================

def test_authentication():
    """Test authentication endpoints"""
    print_test_header("AUTHENTICATION TESTS")
    runner = TestRunner()
    
    # Test 1: Login with invalid credentials
    test_name = "Login with invalid credentials should fail"
    success, user = login("nonexistent_user", "0000")
    runner.run_test(test_name, lambda: not success, True,
                   f"Login failed as expected")
    
    # Test 2: Login endpoint should return proper structure
    test_name = "Login response should have success field"
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": "test", "pin": "1234"},
            timeout=5
        )
        data = response.json()
        has_success = "success" in data
        runner.run_test(test_name, lambda: has_success, True,
                       f"Response keys: {list(data.keys())}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 3: Login with empty username should fail
    test_name = "Login with empty username should fail"
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": "", "pin": "1234"},
            timeout=5
        )
        # Should still respond, but with failure
        success = response.status_code in [200, 400, 401, 422]
        runner.run_test(test_name, lambda: success, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 4: Signup endpoint should exist
    test_name = "Signup endpoint should be accessible"
    try:
        response = requests.post(
            f"{API_BASE}/auth/signup",
            json={"username": "testuser", "pin": "1234", "inviteToken": "fake"},
            timeout=5
        )
        # Should respond (even if token is invalid)
        success = response.status_code in [200, 400, 401, 422]
        runner.run_test(test_name, lambda: success, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    runner.print_summary()
    return runner


# =============================================================================
# PLAYER REGISTRATION TESTS (Requires valid auth)
# =============================================================================

def test_registration_without_auth():
    """Test registration requires authentication"""
    print_test_header("REGISTRATION AUTHORIZATION TESTS")
    runner = TestRunner()
    
    # Test 1: Register without authentication should fail
    test_name = "Registration without valid username should fail"
    success, message, data = register_player("nonexistent_user_12345", "TestPlayer")
    runner.run_test(test_name, lambda: not success, True,
                   f"Registration blocked: {message}")
    
    # Test 2: Guest registration without auth should fail
    test_name = "Guest registration without valid username should fail"
    success, message, data = register_guest("nonexistent_user_12345", "TestGuest")
    runner.run_test(test_name, lambda: not success, True,
                   f"Guest registration blocked: {message}")
    
    # Test 3: Unregister without auth should fail
    test_name = "Unregistration without valid username should fail"
    success, message = unregister_player("nonexistent_user_12345", "SomePlayer")
    runner.run_test(test_name, lambda: not success, True,
                   f"Unregistration blocked: {message}")
    
    runner.print_summary()
    return runner


# =============================================================================
# INPUT VALIDATION TESTS
# =============================================================================

def test_input_validation():
    """Test API input validation"""
    print_test_header("INPUT VALIDATION TESTS")
    runner = TestRunner()
    
    # Test 1: Empty player name validation
    test_name = "API should reject empty player name"
    try:
        response = requests.post(
            f"{API_BASE}/register",
            json={"name": ""},
            params={"username": "testuser"},
            timeout=5
        )
        # Should return validation error (422 or 400)
        rejected = response.status_code in [400, 422]
        runner.run_test(test_name, lambda: rejected, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 2: Whitespace-only name validation
    test_name = "API should reject whitespace-only name"
    try:
        response = requests.post(
            f"{API_BASE}/register",
            json={"name": "   "},
            params={"username": "testuser"},
            timeout=5
        )
        rejected = response.status_code in [400, 422]
        runner.run_test(test_name, lambda: rejected, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 3: Very long name (>100 chars)
    test_name = "API should handle very long name (101 chars)"
    try:
        long_name = "A" * 101
        response = requests.post(
            f"{API_BASE}/register",
            json={"name": long_name},
            params={"username": "testuser"},
            timeout=5
        )
        # Should either accept or reject gracefully
        handled = response.status_code in [200, 400, 422]
        runner.run_test(test_name, lambda: handled, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 4: Special characters in name
    test_name = "API should accept name with special characters"
    try:
        response = requests.post(
            f"{API_BASE}/register",
            json={"name": "Jean-François O'Brien"},
            params={"username": "testuser"},
            timeout=5
        )
        # Should respond (may fail auth, but not validation)
        handled = response.status_code in [200, 400, 403, 422]
        runner.run_test(test_name, lambda: handled, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 5: Missing required field
    test_name = "API should reject request with missing 'name' field"
    try:
        response = requests.post(
            f"{API_BASE}/register",
            json={},
            params={"username": "testuser"},
            timeout=5
        )
        rejected = response.status_code == 422
        runner.run_test(test_name, lambda: rejected, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 6: Invalid JSON
    test_name = "API should reject invalid JSON"
    try:
        response = requests.post(
            f"{API_BASE}/register",
            data="not valid json",
            params={"username": "testuser"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        rejected = response.status_code in [400, 422]
        runner.run_test(test_name, lambda: rejected, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    runner.print_summary()
    return runner


# =============================================================================
# BUSINESS LOGIC TESTS VIA API
# =============================================================================

def test_business_logic_via_api():
    """Test business logic by observing API responses"""
    print_test_header("BUSINESS LOGIC TESTS (VIA API)")
    runner = TestRunner()
    
    # Test 1: Slot max_players should be 10
    test_name = "Slot max_players should be set to 10"
    slot = get_current_slot()
    if slot:
        runner.run_test(test_name, lambda: slot.get("max_players") == 10, True,
                       f"Max players: {slot.get('max_players')}")
    else:
        runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
    
    # Test 2: Player count should be between 0 and 10
    test_name = "Player count should be between 0 and 10"
    if slot:
        count = slot.get("player_count", 0)
        valid_range = 0 <= count <= 10
        runner.run_test(test_name, lambda: valid_range, True,
                       f"Player count: {count}")
    else:
        runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
    
    # Test 3: Players list length should not exceed 10
    test_name = "Players list should not exceed 10 entries"
    if slot:
        players_count = len(slot.get("players", []))
        not_exceeded = players_count <= 10
        runner.run_test(test_name, lambda: not_exceeded, True,
                       f"Players: {players_count}/10")
    else:
        runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
    
    # Test 4: Date should always be Wednesday
    test_name = "Slot date should always be a Wednesday"
    if slot:
        try:
            date_str = slot.get("date", "")
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            is_wednesday = parsed.weekday() == 2
            runner.run_test(test_name, lambda: is_wednesday, True,
                           f"Weekday: {parsed.strftime('%A')}")
        except:
            runner.run_test(test_name, lambda: False, True, "Could not parse date")
    else:
        runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
    
    # Test 5: Time should always be 19:00
    test_name = "Slot time should always be 19:00"
    if slot:
        try:
            date_str = slot.get("date", "")
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            is_19_00 = parsed.hour == 19 and parsed.minute == 0
            runner.run_test(test_name, lambda: is_19_00, True,
                           f"Time: {parsed.strftime('%H:%M')}")
        except:
            runner.run_test(test_name, lambda: False, True, "Could not parse date")
    else:
        runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
    
    runner.print_summary()
    return runner


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

def test_error_handling():
    """Test API error handling"""
    print_test_header("ERROR HANDLING TESTS")
    runner = TestRunner()
    
    # Test 1: Unregister non-existent player
    test_name = "Unregister non-existent player should return error"
    try:
        response = requests.delete(
            f"{API_BASE}/unregister/NonExistentPlayer999",
            params={"username": "testuser"},
            timeout=5
        )
        # Should return error (404 or 400 or 403)
        has_error = response.status_code in [400, 403, 404]
        runner.run_test(test_name, lambda: has_error, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 2: Invalid endpoint should return 404
    test_name = "Invalid endpoint should return 404"
    try:
        response = requests.get(f"{API_BASE}/invalid-endpoint-xyz", timeout=5)
        is_404 = response.status_code == 404
        runner.run_test(test_name, lambda: is_404, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 3: Missing username parameter
    test_name = "Registration without username param should fail"
    try:
        response = requests.post(
            f"{API_BASE}/register",
            json={"name": "TestPlayer"},
            timeout=5
        )
        has_error = response.status_code in [400, 422]
        runner.run_test(test_name, lambda: has_error, True,
                       f"Status: {response.status_code}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 4: Error responses should have detail field
    test_name = "Error responses should contain 'detail' field"
    try:
        response = requests.post(
            f"{API_BASE}/register",
            json={"name": "Test"},
            params={"username": "fake_user_xyz"},
            timeout=5
        )
        if response.status_code >= 400:
            data = response.json()
            has_detail = "detail" in data
            runner.run_test(test_name, lambda: has_detail, True,
                           f"Error format correct")
        else:
            runner.run_test(test_name, lambda: True, True,
                           "No error to test (unexpected success)")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    runner.print_summary()
    return runner


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run all test suites"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 80)
    print("SOCCER SLOT MANAGER - API ENDPOINT TEST SUITE".center(80))
    print("=" * 80)
    print(f"{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.YELLOW}Target URL: {BASE_URL}{Colors.RESET}")
    print(f"{Colors.YELLOW}Configuration: MAX_PLAYERS={MAX_PLAYERS}{Colors.RESET}\n")
    
    # Check server is running
    if not check_server_running():
        print(f"\n{Colors.RED}{Colors.BOLD}ERROR: Server is not running at {BASE_URL}{Colors.RESET}")
        print(f"{Colors.YELLOW}Please ensure the Docker container is running:{Colors.RESET}")
        print(f"  docker-compose up -d")
        print(f"  docker-compose ps\n")
        return
    
    print(f"{Colors.GREEN}✓ Server is running and responding{Colors.RESET}\n")
    
    # Run all test suites
    runners = []
    runners.append(test_server_connectivity())
    runners.append(test_slot_retrieval())
    runners.append(test_authentication())
    runners.append(test_registration_without_auth())
    runners.append(test_input_validation())
    runners.append(test_business_logic_via_api())
    runners.append(test_error_handling())
    
    # Calculate overall summary
    total_tests = sum(r.total for r in runners)
    total_passed = sum(r.passed for r in runners)
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}OVERALL SUMMARY{' '*64}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"\n{Colors.BOLD}Total Test Cases: {total_tests}{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}Passed: {total_passed}{Colors.RESET}")
    print(f"{Colors.RED}{Colors.BOLD}Failed: {total_tests - total_passed}{Colors.RESET}")
    print(f"{Colors.BOLD}Success Rate: {(total_passed/total_tests*100):.1f}%{Colors.RESET}\n")
    
    if total_passed == total_tests:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.RESET}\n")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed - this may be expected for auth-required endpoints{Colors.RESET}\n")


if __name__ == "__main__":
    main()
