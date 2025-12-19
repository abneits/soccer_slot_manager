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
BASE_URL = "http://192.168.0.100:8000"
API_BASE = f"{BASE_URL}/api"
MAX_PLAYERS = 10  # Business rule constant

# Test User Credentials (CONFIGURE THESE FOR YOUR SYSTEM)
# You need to create these users in your system before running tests
ADMIN_USERNAME = "admin"
ADMIN_PIN = "1234"

NORMAL_USER_USERNAME = "testuser"
NORMAL_USER_PIN = "5678"

# Alternative normal user for multi-user tests
NORMAL_USER2_USERNAME = "testuser2"
NORMAL_USER2_PIN = "9999"

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
    def __init__(self, suite_name=""):
        self.total = 0
        self.passed = 0
        self.failed_tests = []  # Track failed tests
        self.suite_name = suite_name
    
    def run_test(self, test_name: str, test_func, expected_result=True, details=""):
        """Run a test and record result"""
        self.total += 1
        try:
            result = test_func()
            passed = (result == expected_result)
            if passed:
                self.passed += 1
            else:
                self.failed_tests.append({
                    'name': test_name,
                    'details': details or f"Expected: {expected_result}, Got: {result}",
                    'suite': self.suite_name
                })
            print_test(test_name, passed, details or f"Expected: {expected_result}, Got: {result}")
        except Exception as e:
            self.failed_tests.append({
                'name': test_name,
                'details': f"Exception: {str(e)}",
                'suite': self.suite_name
            })
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
    runner = TestRunner("Server Connectivity")
    
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
    runner = TestRunner("Slot Retrieval")
    
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
    runner = TestRunner("Authentication")
    
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
        # Check that login actually failed (not just that server responded)
        if response.status_code == 200:
            data = response.json()
            login_failed = not data.get("success", True)
        else:
            login_failed = response.status_code in [400, 401, 422]
        
        runner.run_test(test_name, lambda: login_failed, True,
                       f"Status: {response.status_code}, Login rejected: {login_failed}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 4: Signup endpoint should reject invalid invite token
    test_name = "Signup endpoint should reject invalid invite token"
    try:
        response = requests.post(
            f"{API_BASE}/auth/signup",
            json={"username": "testuser", "pin": "1234", "inviteToken": "fake"},
            timeout=5
        )
        # Should reject with error status (not 200)
        rejected = response.status_code in [400, 401, 403, 422]
        runner.run_test(test_name, lambda: rejected, True,
                       f"Status: {response.status_code}, Rejected: {rejected}")
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
    runner = TestRunner("Registration Authorization")
    
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
    runner = TestRunner("Input Validation")
    
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
    runner = TestRunner("Business Logic")
    
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
    
    runner.print_summary()
    return runner


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

def test_error_handling():
    """Test API error handling"""
    print_test_header("ERROR HANDLING TESTS")
    runner = TestRunner("Error Handling")
    
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
# AUTHENTICATED USER TESTS - NORMAL USER
# =============================================================================

def test_normal_user_authentication():
    """Test normal user login and authentication"""
    print_test_header("NORMAL USER AUTHENTICATION TESTS")
    runner = TestRunner("Normal User Authentication")
    
    # Test 1: Login with valid normal user credentials
    test_name = f"Login as normal user '{NORMAL_USER_USERNAME}' should succeed"
    success, user_data = login(NORMAL_USER_USERNAME, NORMAL_USER_PIN)
    runner.run_test(test_name, lambda: success, True,
                   f"User: {user_data if success else 'Login failed'}")
    
    if success and user_data:
        # Test 2: User should have username field
        test_name = "User data should contain username"
        runner.run_test(test_name, lambda: "username" in user_data, True,
                       f"Username: {user_data.get('username')}")
        
        # Test 3: User should have role field
        test_name = "User data should contain role"
        runner.run_test(test_name, lambda: "role" in user_data, True,
                       f"Role: {user_data.get('role')}")
        
        # Test 4: Normal user role should not be 'admin'
        test_name = "Normal user role should be 'user' (not 'admin')"
        is_user = user_data.get("role") == "user"
        runner.run_test(test_name, lambda: is_user, True,
                       f"Role: {user_data.get('role')}")
    
    # Test 5: Login with wrong PIN should fail
    test_name = "Login with correct username but wrong PIN should fail"
    success, user_data = login(NORMAL_USER_USERNAME, "0000")
    runner.run_test(test_name, lambda: not success, True,
                   f"Failed as expected")
    
    runner.print_summary()
    return runner


def test_normal_user_registration():
    """Test normal user player registration flow"""
    print_test_header("NORMAL USER - PLAYER REGISTRATION TESTS")
    runner = TestRunner("Normal User Registration")
    
    # First, unregister if already registered
    unregister_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    time.sleep(0.3)
    
    # Get initial slot state
    initial_slot = get_current_slot()
    initial_count = initial_slot.get("player_count", 0) if initial_slot else 0
    
    # Test 1: Register as normal user
    test_name = f"Normal user '{NORMAL_USER_USERNAME}' should register successfully"
    success, message, data = register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    runner.run_test(test_name, lambda: success, True,
                   f"Registration: {message if not success else 'Success'}")
    
    if success and data:
        # Test 2: Player count should increase
        test_name = "Player count should increase after registration"
        new_count = data.get("player_count", 0)
        increased = new_count > initial_count or NORMAL_USER_USERNAME in data.get("players", [])
        runner.run_test(test_name, lambda: increased, True,
                       f"Count: {initial_count} → {new_count}")
        
        # Test 3: User should appear in players list
        test_name = "User should appear in players list"
        players = data.get("players", [])
        in_list = NORMAL_USER_USERNAME in players
        runner.run_test(test_name, lambda: in_list, True,
                       f"Players: {players}")
    
    # Test 4: Try to register again (should fail - duplicate)
    test_name = "Duplicate registration should be rejected"
    success2, message2, _ = register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    runner.run_test(test_name, lambda: not success2, True,
                   f"Rejected: {message2}")
    
    runner.print_summary()
    return runner


def test_normal_user_guest_registration():
    """Test normal user guest registration"""
    print_test_header("NORMAL USER - GUEST REGISTRATION TESTS")
    runner = TestRunner("Normal User Guest Registration")
    
    guest_name = f"GuestUser_{random.randint(1000, 9999)}"
    
    # Test 1: Register a guest
    test_name = f"Normal user should be able to register a guest '{guest_name}'"
    success, message, data = register_guest(NORMAL_USER_USERNAME, guest_name)
    runner.run_test(test_name, lambda: success, True,
                   f"Guest registration: {message if not success else 'Success'}")
    
    if success and data:
        # Test 2: Guest should appear in players list with (Invité) prefix
        test_name = "Guest should appear with '(Invité)' prefix"
        players = data.get("players", [])
        guest_in_list = any(guest_name in p and "(Invité)" in p for p in players)
        runner.run_test(test_name, lambda: guest_in_list, True,
                       f"Guest found: {guest_in_list}")
        
        # Test 3: Guest entry should show who invited them
        test_name = f"Guest entry should show invited by '{NORMAL_USER_USERNAME}'"
        guest_entry = next((p for p in players if guest_name in p), None)
        shows_inviter = guest_entry and NORMAL_USER_USERNAME in guest_entry
        runner.run_test(test_name, lambda: shows_inviter, True,
                       f"Entry: {guest_entry}")
    
    # Test 4: Try to register same guest name again (should fail)
    test_name = "Duplicate guest name should be rejected"
    success2, message2, _ = register_guest(NORMAL_USER_USERNAME, guest_name)
    runner.run_test(test_name, lambda: not success2, True,
                   f"Rejected: {message2}")
    
    runner.print_summary()
    return runner


def test_normal_user_unregistration():
    """Test normal user unregistration flow"""
    print_test_header("NORMAL USER - UNREGISTRATION TESTS")
    runner = TestRunner("Normal User Unregistration")
    
    # First, ensure user is registered
    register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    time.sleep(0.5)
    
    # Test 1: User should be able to unregister themselves
    test_name = f"User should be able to unregister themselves"
    success, message = unregister_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    runner.run_test(test_name, lambda: success, True,
                   f"Unregistration: {message if not success else 'Success'}")
    
    if success:
        # Test 2: User should not appear in players list after unregistration
        test_name = "User should not appear in list after unregistration"
        slot = get_current_slot()
        if slot:
            players = slot.get("players", [])
            not_in_list = NORMAL_USER_USERNAME not in players
            runner.run_test(test_name, lambda: not_in_list, True,
                           f"User removed: {not_in_list}")
        else:
            runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
    
    # Test 3: Try to unregister when not registered (should fail)
    test_name = "Unregister when not registered should fail"
    time.sleep(0.5)
    success2, message2 = unregister_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    runner.run_test(test_name, lambda: not success2, True,
                   f"Error: {message2}")
    
    runner.print_summary()
    return runner


def test_normal_user_cannot_remove_others():
    """Test that normal user cannot remove other players"""
    print_test_header("NORMAL USER - PERMISSION TESTS")
    runner = TestRunner("Normal User Permissions")
    
    # Ensure both users are registered
    register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    register_player(NORMAL_USER2_USERNAME, NORMAL_USER2_USERNAME)
    time.sleep(0.5)
    
    # Test 1: Normal user should NOT be able to remove another user
    test_name = f"'{NORMAL_USER_USERNAME}' should NOT remove '{NORMAL_USER2_USERNAME}'"
    success, message = unregister_player(NORMAL_USER_USERNAME, NORMAL_USER2_USERNAME)
    runner.run_test(test_name, lambda: not success, True,
                   f"Blocked: {message}")
    
    # Test 2: Error should mention permission/authorization
    test_name = "Error message should indicate permission issue"
    has_permission_error = success == False and ("permission" in message.lower() or "supprimer" in message.lower() or "403" in str(message))
    runner.run_test(test_name, lambda: has_permission_error, True,
                   f"Message: {message}")
    
    runner.print_summary()
    return runner


# =============================================================================
# AUTHENTICATED USER TESTS - ADMIN USER
# =============================================================================

def test_admin_authentication():
    """Test admin user login and authentication"""
    print_test_header("ADMIN USER AUTHENTICATION TESTS")
    runner = TestRunner("Admin Authentication")
    
    # Test 1: Login with valid admin credentials
    test_name = f"Login as admin user '{ADMIN_USERNAME}' should succeed"
    success, user_data = login(ADMIN_USERNAME, ADMIN_PIN)
    runner.run_test(test_name, lambda: success, True,
                   f"User: {user_data if success else 'Login failed'}")
    
    if success and user_data:
        # Test 2: Admin should have username field
        test_name = "Admin data should contain username"
        runner.run_test(test_name, lambda: "username" in user_data, True,
                       f"Username: {user_data.get('username')}")
        
        # Test 3: Admin should have role field
        test_name = "Admin data should contain role"
        runner.run_test(test_name, lambda: "role" in user_data, True,
                       f"Role: {user_data.get('role')}")
        
        # Test 4: Admin role should be 'admin'
        test_name = "Admin user role should be 'admin'"
        is_admin = user_data.get("role") == "admin"
        runner.run_test(test_name, lambda: is_admin, True,
                       f"Role: {user_data.get('role')}")
    
    runner.print_summary()
    return runner


def test_admin_registration():
    """Test admin user player registration"""
    print_test_header("ADMIN USER - REGISTRATION TESTS")
    runner = TestRunner("Admin Registration")
    
    # Test 1: Admin can register themselves
    test_name = f"Admin '{ADMIN_USERNAME}' should register successfully"
    success, message, data = register_player(ADMIN_USERNAME, ADMIN_USERNAME)
    runner.run_test(test_name, lambda: success, True,
                   f"Registration: {message if not success else 'Success'}")
    
    if success and data:
        # Test 2: Admin should appear in players list
        test_name = "Admin should appear in players list"
        players = data.get("players", [])
        in_list = ADMIN_USERNAME in players
        runner.run_test(test_name, lambda: in_list, True,
                       f"Admin in list: {in_list}")
    
    runner.print_summary()
    return runner


def test_admin_can_remove_any_player():
    """Test that admin can remove any player"""
    print_test_header("ADMIN USER - REMOVAL PERMISSION TESTS")
    runner = TestRunner("Admin Removal Permissions")
    
    # Ensure normal user is registered
    register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    time.sleep(0.5)
    
    # Test 1: Admin SHOULD be able to remove any user
    test_name = f"Admin should be able to remove '{NORMAL_USER_USERNAME}'"
    success, message = unregister_player(ADMIN_USERNAME, NORMAL_USER_USERNAME)
    runner.run_test(test_name, lambda: success, True,
                   f"Removal: {message if not success else 'Success'}")
    
    if success:
        # Test 2: User should be removed from list
        test_name = "User should be removed from players list"
        slot = get_current_slot()
        if slot:
            players = slot.get("players", [])
            not_in_list = NORMAL_USER_USERNAME not in players
            runner.run_test(test_name, lambda: not_in_list, True,
                           f"Removed: {not_in_list}")
        else:
            runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
    
    runner.print_summary()
    return runner


def test_admin_guest_management():
    """Test admin guest registration and removal"""
    print_test_header("ADMIN USER - GUEST MANAGEMENT TESTS")
    runner = TestRunner("Admin Guest Management")
    
    guest_name = f"AdminGuest_{random.randint(1000, 9999)}"
    
    # Test 1: Admin can register guests
    test_name = f"Admin should be able to register guest '{guest_name}'"
    success, message, data = register_guest(ADMIN_USERNAME, guest_name)
    runner.run_test(test_name, lambda: success, True,
                   f"Guest registration: {message if not success else 'Success'}")
    
    if success and data:
        # Test 2: Admin can remove any guest (including those invited by others)
        test_name = "Admin should be able to remove any guest"
        
        # Find the guest entry in the players list
        players = data.get("players", [])
        guest_entry = next((p for p in players if guest_name in p), None)
        
        if guest_entry:
            success_remove, message_remove = unregister_player(ADMIN_USERNAME, guest_entry)
            runner.run_test(test_name, lambda: success_remove, True,
                           f"Guest removal: {message_remove if not success_remove else 'Success'}")
        else:
            runner.run_test(test_name, lambda: False, True, "Guest not found in list")
    
    runner.print_summary()
    return runner


# =============================================================================
# FULL USER JOURNEY TESTS
# =============================================================================

def test_complete_user_journey():
    """Test complete user journey from login to registration to unregistration"""
    print_test_header("COMPLETE USER JOURNEY TESTS")
    runner = TestRunner("Complete User Journey")
    
    journey_user = NORMAL_USER2_USERNAME
    journey_pin = NORMAL_USER2_PIN
    
    # Pre-step: Unregister if already registered
    unregister_player(journey_user, journey_user)
    time.sleep(0.3)
    
    # Step 1: Login
    test_name = f"Step 1: User '{journey_user}' logs in"
    success_login, user_data = login(journey_user, journey_pin)
    runner.run_test(test_name, lambda: success_login, True,
                   f"Login: {'Success' if success_login else 'Failed'}")
    
    if success_login:
        # Step 2: Check current slot
        test_name = "Step 2: User views current slot"
        slot = get_current_slot()
        runner.run_test(test_name, lambda: slot is not None, True,
                       f"Slot date: {slot.get('date') if slot else 'N/A'}")
        
        # Step 3: Register for slot
        test_name = "Step 3: User registers for slot"
        success_reg, msg_reg, data_reg = register_player(journey_user, journey_user)
        runner.run_test(test_name, lambda: success_reg, True,
                       f"Registration: {msg_reg if not success_reg else 'Success'}")
        
        if success_reg:
            # Step 4: Verify registration
            test_name = "Step 4: User appears in slot"
            slot_after = get_current_slot()
            in_slot = journey_user in slot_after.get("players", []) if slot_after else False
            runner.run_test(test_name, lambda: in_slot, True,
                           f"In slot: {in_slot}")
            
            # Step 5: Register a guest
            guest_name = f"Journey_Guest_{random.randint(100, 999)}"
            test_name = f"Step 5: User registers guest '{guest_name}'"
            success_guest, msg_guest, data_guest = register_guest(journey_user, guest_name)
            runner.run_test(test_name, lambda: success_guest, True,
                           f"Guest: {msg_guest if not success_guest else 'Success'}")
            
            # Step 6: Verify guest appears
            if success_guest:
                test_name = "Step 6: Guest appears in slot"
                slot_with_guest = get_current_slot()
                guest_in_slot = any(guest_name in p for p in slot_with_guest.get("players", [])) if slot_with_guest else False
                runner.run_test(test_name, lambda: guest_in_slot, True,
                               f"Guest in slot: {guest_in_slot}")
                
                # Step 7: Remove guest
                if guest_in_slot:
                    guest_entry = next((p for p in slot_with_guest.get("players", []) if guest_name in p), None)
                    test_name = "Step 7: User removes their guest"
                    success_remove_guest, msg_remove_guest = unregister_player(journey_user, guest_entry)
                    runner.run_test(test_name, lambda: success_remove_guest, True,
                                   f"Guest removal: {msg_remove_guest if not success_remove_guest else 'Success'}")
            
            # Step 8: Unregister self
            test_name = "Step 8: User unregisters themselves"
            success_unreg, msg_unreg = unregister_player(journey_user, journey_user)
            runner.run_test(test_name, lambda: success_unreg, True,
                           f"Unregistration: {msg_unreg if not success_unreg else 'Success'}")
            
            # Step 9: Verify unregistration
            if success_unreg:
                test_name = "Step 9: User no longer appears in slot"
                final_slot = get_current_slot()
                not_in_slot = journey_user not in final_slot.get("players", []) if final_slot else True
                runner.run_test(test_name, lambda: not_in_slot, True,
                               f"Removed: {not_in_slot}")
    
    runner.print_summary()
    return runner



def test_multi_user_interactions():
    """Test interactions between multiple users"""
    print_test_header("MULTI-USER INTERACTION TESTS")
    runner = TestRunner("Multi-User Interactions")
    
    # Ensure both users are not registered initially
    unregister_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    unregister_player(NORMAL_USER2_USERNAME, NORMAL_USER2_USERNAME)
    time.sleep(0.5)
    
    # Test 1: First user registers
    test_name = f"User 1 '{NORMAL_USER_USERNAME}' registers"
    success1, _, data1 = register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    runner.run_test(test_name, lambda: success1, True,
                   f"User 1 registered: {success1}")
    
    # Test 2: Second user registers
    test_name = f"User 2 '{NORMAL_USER2_USERNAME}' registers"
    success2, _, data2 = register_player(NORMAL_USER2_USERNAME, NORMAL_USER2_USERNAME)
    runner.run_test(test_name, lambda: success2, True,
                   f"User 2 registered: {success2}")
    
    if success1 and success2:
        # Test 3: Both users should appear in slot
        test_name = "Both users should appear in players list"
        slot = get_current_slot()
        if slot:
            players = slot.get("players", [])
            both_present = NORMAL_USER_USERNAME in players and NORMAL_USER2_USERNAME in players
            runner.run_test(test_name, lambda: both_present, True,
                           f"Players: {players}")
        else:
            runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
        
        # Test 4: User 1 cannot remove User 2
        test_name = "User 1 should NOT be able to remove User 2"
        success_remove, msg = unregister_player(NORMAL_USER_USERNAME, NORMAL_USER2_USERNAME)
        runner.run_test(test_name, lambda: not success_remove, True,
                       f"Blocked: {msg}")
        
        # Test 5: User 2 can remove themselves
        test_name = "User 2 can remove themselves"
        success_self_remove, _ = unregister_player(NORMAL_USER2_USERNAME, NORMAL_USER2_USERNAME)
        runner.run_test(test_name, lambda: success_self_remove, True,
                       f"Self removal: {success_self_remove}")
    
    runner.print_summary()
    return runner


def test_progressive_slot_filling():
    """Test slot filling progressively from empty to full"""
    print_test_header("PROGRESSIVE SLOT FILLING TESTS")
    runner = TestRunner("Progressive Slot Filling")
    
    print(f"{Colors.YELLOW}⚠️  NOTE: This test will clear and progressively fill the slot{Colors.RESET}\n")
    
    # Step 1: Clear the slot by removing all players
    test_name = "Step 1: Clear slot (remove all existing players)"
    slot = get_current_slot()
    initial_count = slot.get("player_count", 0) if slot else 0
    
    if slot and initial_count > 0:
        # Try to remove all players using admin account
        players = slot.get("players", [])
        for player in players:
            unregister_player(ADMIN_USERNAME, player)
        time.sleep(0.5)
        slot = get_current_slot()
        cleared = slot.get("player_count", 0) == 0 if slot else False
        runner.run_test(test_name, lambda: cleared, True,
                       f"Initial: {initial_count}, After clear: {slot.get('player_count', 0) if slot else 'N/A'}")
    else:
        runner.run_test(test_name, lambda: True, True,
                       f"Slot already empty")
    
    # Get fresh slot state
    slot = get_current_slot()
    if not slot:
        runner.run_test("Could not retrieve slot", lambda: False, True, "Aborting progressive fill tests")
        runner.print_summary()
        return runner
    
    # Step 2: Register primary user (0 → 1)
    test_name = "Step 2: Slot accepts 1st player (0 → 1)"
    success1, _, data1 = register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    count_after_1 = data1.get("player_count", 0) if data1 else 0
    runner.run_test(test_name, lambda: success1 and count_after_1 == 1, True,
                   f"Success: {success1}, Count: {count_after_1}/10")
    
    # Step 3: Register second user (1 → 2)
    test_name = "Step 3: Slot accepts 2nd player (1 → 2)"
    success2, _, data2 = register_player(NORMAL_USER2_USERNAME, NORMAL_USER2_USERNAME)
    count_after_2 = data2.get("player_count", 0) if data2 else 0
    runner.run_test(test_name, lambda: success2 and count_after_2 == 2, True,
                   f"Success: {success2}, Count: {count_after_2}/10")
    time.sleep(0.2)
    
    # Step 4: Register admin user (2 → 3)
    test_name = "Step 4: Slot accepts 3rd player (2 → 3)"
    success3, _, data3 = register_player(ADMIN_USERNAME, ADMIN_USERNAME)
    count_after_3 = data3.get("player_count", 0) if data3 else 0
    runner.run_test(test_name, lambda: success3 and count_after_3 == 3, True,
                   f"Success: {success3}, Count: {count_after_3}/10")
    time.sleep(0.2)
    
    # Step 5-11: Fill remaining slots with guests (3 → 10)
    for i in range(4, 11):
        test_name = f"Step {i+1}: Slot accepts player {i} via guest ({i-1} → {i})"
        guest_name = f"Guest_{i}_{random.randint(100,999)}"
        success, _, data = register_guest(NORMAL_USER_USERNAME, guest_name)
        count = data.get("player_count", 0) if data else 0
        runner.run_test(test_name, lambda s=success, c=count, expected=i: s and c == expected, True,
                       f"Success: {success}, Count: {count}/10")
        time.sleep(0.2)  # Small delay between registrations
    
    # Verify slot is now full
    slot_full = get_current_slot()
    final_count = slot_full.get("player_count", 0) if slot_full else 0
    
    # Step 12: Verify slot is full (count = 10)
    test_name = "Step 12: Verify slot is exactly full (10/10)"
    runner.run_test(test_name, lambda: final_count == 10, True,
                   f"Final count: {final_count}/10")
    
    # Step 13: Test slot rejects 11th guest when full
    test_name = "Step 13: Slot rejects 11th guest when full"
    success_11, message_11, _ = register_guest(NORMAL_USER_USERNAME, f"Guest_11_{random.randint(100,999)}")
    runner.run_test(test_name, lambda: not success_11, True,
                   f"Rejected: {message_11}")
    
    # Step 14: Verify rejection message mentions "full" or "complet"
    test_name = "Step 14: Rejection message indicates slot is full"
    has_full_message = "complet" in message_11.lower() or "full" in message_11.lower()
    runner.run_test(test_name, lambda: has_full_message, True,
                   f"Message: {message_11}")
    
    # Step 15: Count should still be 10 after rejection
    test_name = "Step 15: Player count remains 10 after rejection"
    slot_after_reject = get_current_slot()
    count_after_reject = slot_after_reject.get("player_count", 0) if slot_after_reject else 0
    runner.run_test(test_name, lambda: count_after_reject == 10, True,
                   f"Count: {count_after_reject}/10")
    
    # Step 16: Remove one player to free a spot
    test_name = "Step 16: Remove one player (10 → 9)"
    if slot_after_reject:
        players = slot_after_reject.get("players", [])
        if players:
            player_to_remove = players[0]  # Remove first player
            success_remove, _ = unregister_player(ADMIN_USERNAME, player_to_remove)
            time.sleep(0.3)
            slot_after_remove = get_current_slot()
            count_after_remove = slot_after_remove.get("player_count", 0) if slot_after_remove else 0
            runner.run_test(test_name, lambda: success_remove and count_after_remove == 9, True,
                           f"Removed: {success_remove}, Count: {count_after_remove}/10")
        else:
            runner.run_test(test_name, lambda: False, True, "No players to remove")
    
    # Step 17: Slot should accept new guest after spot freed (9 → 10)
    test_name = "Step 17: Slot accepts guest after spot freed (9 → 10)"
    success_refill, _, data_refill = register_guest(NORMAL_USER_USERNAME, f"Guest_Refill_{random.randint(100,999)}")
    count_refill = data_refill.get("player_count", 0) if data_refill else 0
    runner.run_test(test_name, lambda: success_refill and count_refill == 10, True,
                   f"Success: {success_refill}, Count: {count_refill}/10")
    
    # Step 18: Slot should be full again
    test_name = "Step 18: Slot is full again after refill"
    slot_final = get_current_slot()
    final_count_2 = slot_final.get("player_count", 0) if slot_final else 0
    runner.run_test(test_name, lambda: final_count_2 == 10, True,
                   f"Final count: {final_count_2}/10")
    
    runner.print_summary()
    return runner


def test_full_slot_behavior():
    """Test various operations when slot is full"""
    print_test_header("FULL SLOT BEHAVIOR TESTS")
    runner = TestRunner("Full Slot Behavior")
    
    # Ensure slot is full first
    slot = get_current_slot()
    if not slot:
        runner.run_test("Could not retrieve slot", lambda: False, True, "Aborting full slot tests")
        runner.print_summary()
        return runner
    
    current_count = slot.get("player_count", 0)
    
    # Fill slot if not already full using guests
    if current_count < 10:
        print(f"{Colors.YELLOW}Filling slot to capacity with guests...{Colors.RESET}")
        spots_needed = 10 - current_count
        for i in range(spots_needed):
            register_guest(NORMAL_USER_USERNAME, f"FillGuest_{i}_{random.randint(100,999)}")
            time.sleep(0.2)
        slot = get_current_slot()
        current_count = slot.get("player_count", 0) if slot else 0
    
    # Test 1: Verify slot is full
    test_name = "Verify slot is at maximum capacity (10/10)"
    runner.run_test(test_name, lambda: current_count == 10, True,
                   f"Current count: {current_count}/10")
    
    # Test 2: Guest registration should fail when full
    test_name = "Guest registration should fail when full"
    success2, msg2, _ = register_guest(NORMAL_USER_USERNAME, f"NewGuest_{random.randint(1000,9999)}")
    runner.run_test(test_name, lambda: not success2, True,
                   f"Blocked: {msg2}")
    
    # Test 3: Another guest registration should also fail when full
    test_name = "Another guest registration should fail when full"
    success3, msg3, _ = register_guest(NORMAL_USER2_USERNAME, f"AnotherGuest_{random.randint(1000,9999)}")
    runner.run_test(test_name, lambda: not success3, True,
                   f"Blocked: {msg3}")
    
    # Test 4: Multiple guest registration attempts should all fail
    test_name = "Multiple rapid guest registration attempts should all fail"
    attempts = []
    for i in range(3):
        success, _, _ = register_guest(NORMAL_USER_USERNAME, f"GuestAttempt_{i}_{random.randint(1000,9999)}")
        attempts.append(success)
        time.sleep(0.1)
    all_failed = all(not s for s in attempts)
    runner.run_test(test_name, lambda: all_failed, True,
                   f"All 3 attempts failed: {all_failed}")
    
    # Test 6: Slot data retrieval still works when full
    test_name = "Slot data retrieval works when full"
    slot_data = get_current_slot()
    retrieval_works = slot_data is not None
    runner.run_test(test_name, lambda: retrieval_works, True,
                   f"Data retrieved: {retrieval_works}")
    
    # Test 7: Players list has exactly 10 entries
    test_name = "Players list contains exactly 10 entries"
    if slot_data:
        players_list = slot_data.get("players", [])
        has_10 = len(players_list) == 10
        runner.run_test(test_name, lambda: has_10, True,
                       f"List length: {len(players_list)}")
    else:
        runner.run_test(test_name, lambda: False, True, "No slot data")
    
    # Test 8: Admin can still remove players when full
    test_name = "Admin can remove player even when slot is full"
    if slot_data:
        players = slot_data.get("players", [])
        if players:
            success_admin_remove, _ = unregister_player(ADMIN_USERNAME, players[0])
            runner.run_test(test_name, lambda: success_admin_remove, True,
                           f"Admin removal: {success_admin_remove}")
            
            # Test 9: Spot should be available after admin removal
            if success_admin_remove:
                time.sleep(0.3)
                test_name = "Spot available after admin removes player"
                slot_after = get_current_slot()
                count_after = slot_after.get("player_count", 0) if slot_after else 0
                runner.run_test(test_name, lambda: count_after == 9, True,
                               f"Count after removal: {count_after}/10")
                
                # Test 10: New guest registration should succeed after spot freed
                test_name = "New guest registration succeeds after spot freed"
                success_new, _, _ = register_guest(NORMAL_USER_USERNAME, f"GuestAfterRemoval_{random.randint(1000,9999)}")
                runner.run_test(test_name, lambda: success_new, True,
                               f"Registration: {success_new}")
        else:
            runner.run_test(test_name, lambda: False, True, "No players to remove")
    else:
        runner.run_test(test_name, lambda: False, True, "No slot data")
    
    runner.print_summary()
    return runner


def test_guest_permission_boundaries():
    """Test guest removal permissions in detail"""
    print_test_header("GUEST PERMISSION BOUNDARY TESTS")
    runner = TestRunner("Guest Permission Boundaries")
    
    guest1_name = f"User1Guest_{random.randint(1000, 9999)}"
    guest2_name = f"User2Guest_{random.randint(1000, 9999)}"
    
    # Setup: Register two guests by different users
    register_guest(NORMAL_USER_USERNAME, guest1_name)
    register_guest(NORMAL_USER2_USERNAME, guest2_name)
    time.sleep(0.3)
    
    slot = get_current_slot()
    if not slot:
        runner.run_test("Could not retrieve slot", lambda: False, True, "Aborting guest permission tests")
        runner.print_summary()
        return runner
    
    players = slot.get("players", [])
    guest1_entry = next((p for p in players if guest1_name in p), None)
    guest2_entry = next((p for p in players if guest2_name in p), None)
    
    # Test 1: User can remove their own guest
    test_name = f"User 1 can remove their own guest '{guest1_name}'"
    if guest1_entry:
        success1, msg1 = unregister_player(NORMAL_USER_USERNAME, guest1_entry)
        runner.run_test(test_name, lambda: success1, True,
                       f"Removal: {msg1 if not success1 else 'Success'}")
    else:
        runner.run_test(test_name, lambda: False, True, "Guest 1 not found")
    
    # Test 2: User cannot remove another user's guest
    test_name = f"User 1 cannot remove User 2's guest '{guest2_name}'"
    if guest2_entry:
        success2, msg2 = unregister_player(NORMAL_USER_USERNAME, guest2_entry)
        runner.run_test(test_name, lambda: not success2, True,
                       f"Blocked: {msg2}")
    else:
        runner.run_test(test_name, lambda: False, True, "Guest 2 not found")
    
    # Test 3: Admin can remove any guest
    test_name = f"Admin can remove any user's guest"
    if guest2_entry:
        success3, msg3 = unregister_player(ADMIN_USERNAME, guest2_entry)
        runner.run_test(test_name, lambda: success3, True,
                       f"Admin removal: {msg3 if not success3 else 'Success'}")
    else:
        runner.run_test(test_name, lambda: False, True, "Guest 2 not found")
    
    runner.print_summary()
    return runner


def test_timestamp_validation():
    """Test that timestamps are present and valid"""
    print_test_header("TIMESTAMP VALIDATION TESTS")
    runner = TestRunner("Timestamp Validation")
    
    # Clear and register fresh
    slot = get_current_slot()
    if slot:
        players = slot.get("players", [])
        for player in players:
            unregister_player(ADMIN_USERNAME, player)
    time.sleep(0.5)
    
    # Register a player
    register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    time.sleep(0.3)
    
    slot = get_current_slot()
    if not slot:
        runner.run_test("Could not retrieve slot", lambda: False, True, "Aborting timestamp tests")
        runner.print_summary()
        return runner
    
    # Test 1: Response should have timestamps field
    test_name = "Slot response should contain 'timestamps' field"
    has_timestamps = "timestamps" in slot
    runner.run_test(test_name, lambda: has_timestamps, True,
                   f"Has timestamps: {has_timestamps}")
    
    if has_timestamps:
        timestamps = slot.get("timestamps", [])
        
        # Test 2: Timestamps should be a list
        test_name = "Timestamps should be a list"
        runner.run_test(test_name, lambda: isinstance(timestamps, list), True,
                       f"Type: {type(timestamps)}")
        
        # Test 3: Timestamps count should match player count
        test_name = "Timestamps count should match player count"
        player_count = slot.get("player_count", 0)
        timestamp_count = len(timestamps)
        runner.run_test(test_name, lambda: timestamp_count == player_count, True,
                       f"Players: {player_count}, Timestamps: {timestamp_count}")
        
        # Test 4: Each timestamp should be valid ISO format
        if timestamps:
            test_name = "All timestamps should be valid ISO 8601 format"
            try:
                for ts in timestamps:
                    datetime.fromisoformat(ts.replace('Z', '+00:00'))
                runner.run_test(test_name, lambda: True, True,
                               f"All {len(timestamps)} timestamps valid")
            except:
                runner.run_test(test_name, lambda: False, True,
                               f"Invalid timestamp format found")
    
    runner.print_summary()
    return runner


def test_data_consistency():
    """Test data consistency across operations"""
    print_test_header("DATA CONSISTENCY TESTS")
    runner = TestRunner("Data Consistency")
    
    # Test 1: Player count always matches list length
    test_name = "Player count field always matches actual list length"
    slot = get_current_slot()
    if slot:
        player_count = slot.get("player_count", 0)
        players_length = len(slot.get("players", []))
        runner.run_test(test_name, lambda: player_count == players_length, True,
                       f"Count: {player_count}, Length: {players_length}")
    else:
        runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
    
    # Test 2: No duplicate players in list
    test_name = "No duplicate players in players list"
    if slot:
        players = slot.get("players", [])
        unique_players = list(set(players))
        has_no_duplicates = len(players) == len(unique_players)
        runner.run_test(test_name, lambda: has_no_duplicates, True,
                       f"Players: {len(players)}, Unique: {len(unique_players)}")
    else:
        runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
    
    # Test 3: Register and immediately check consistency
    test_name = "Consistency maintained after registration"
    unregister_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    time.sleep(0.3)
    success, _, data = register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    if success and data:
        count = data.get("player_count", 0)
        length = len(data.get("players", []))
        consistent = count == length
        runner.run_test(test_name, lambda: consistent, True,
                       f"After registration - Count: {count}, Length: {length}")
    else:
        runner.run_test(test_name, lambda: False, True, "Registration failed")
    
    # Test 4: Consistency after unregistration
    test_name = "Consistency maintained after unregistration"
    success_unreg, _ = unregister_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    if success_unreg:
        time.sleep(0.3)
        slot_after = get_current_slot()
        if slot_after:
            count_after = slot_after.get("player_count", 0)
            length_after = len(slot_after.get("players", []))
            consistent_after = count_after == length_after
            runner.run_test(test_name, lambda: consistent_after, True,
                           f"After unregistration - Count: {count_after}, Length: {length_after}")
        else:
            runner.run_test(test_name, lambda: False, True, "Could not retrieve slot")
    
    runner.print_summary()
    return runner


def test_boundary_conditions():
    """Test specific boundary conditions"""
    print_test_header("BOUNDARY CONDITION TESTS")
    runner = TestRunner("Boundary Conditions")
    
    # Get current state
    slot = get_current_slot()
    if not slot:
        runner.run_test("Could not retrieve slot", lambda: False, True, "Aborting boundary tests")
        runner.print_summary()
        return runner
    
    current_count = slot.get("player_count", 0)
    
    # Test 1: Slot at exactly 9/10 should accept one more
    if current_count < 9:
        # Fill to 9
        print(f"{Colors.YELLOW}Setting up 9/10 scenario...{Colors.RESET}")
        spots_to_add = 9 - current_count
        for i in range(spots_to_add):
            register_guest(NORMAL_USER_USERNAME, f"Boundary_{i}_{random.randint(100,999)}")
            time.sleep(0.1)
    
    slot = get_current_slot()
    if slot and slot.get("player_count", 0) == 9:
        test_name = "Slot at 9/10 should accept exactly one more player"
        success, _, data = register_guest(NORMAL_USER_USERNAME, f"FinalSpot_{random.randint(100,999)}")
        if success and data:
            final_count = data.get("player_count", 0)
            runner.run_test(test_name, lambda: success and final_count == 10, True,
                           f"Accepted: {success}, Final count: {final_count}/10")
        else:
            runner.run_test(test_name, lambda: False, True, "Failed to add final player")
    
    # Test 2: Empty slot (0/10) accepts first player
    # Clear the slot first
    slot = get_current_slot()
    if slot:
        players = slot.get("players", [])
        for player in players:
            unregister_player(ADMIN_USERNAME, player)
        time.sleep(0.5)
    
    test_name = "Empty slot (0/10) accepts first player"
    success_first, _, data_first = register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    if success_first and data_first:
        count_first = data_first.get("player_count", 0)
        runner.run_test(test_name, lambda: success_first and count_first == 1, True,
                       f"First player added: {success_first}, Count: {count_first}/10")
    else:
        runner.run_test(test_name, lambda: False, True, "Failed to add first player")
    
    # Test 3: Slot with space (< 10) returns correct available spots
    slot = get_current_slot()
    if slot:
        count = slot.get("player_count", 0)
        max_players = slot.get("max_players", 10)
        available = max_players - count
        
        test_name = f"Slot with {count}/10 shows {available} available spots"
        runner.run_test(test_name, lambda: available >= 0, True,
                       f"Current: {count}/10, Available: {available}")
    
    runner.print_summary()
    return runner


def test_error_message_quality():
    """Test that error messages are informative and in French"""
    print_test_header("ERROR MESSAGE QUALITY TESTS")
    runner = TestRunner("Error Message Quality")
    
    # Test 1: Duplicate registration error is in French
    test_name = "Duplicate registration error is in French"
    register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    time.sleep(0.3)
    success, message, _ = register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    if not success:
        is_french = any(word in message.lower() for word in ["déjà", "deja", "inscrit"])
        runner.run_test(test_name, lambda: is_french, True,
                       f"Message: {message}")
    else:
        runner.run_test(test_name, lambda: False, True, "Expected error did not occur")
    
    # Test 2: Full slot error is in French
    test_name = "Full slot error is in French"
    # Fill slot first
    slot = get_current_slot()
    if slot and slot.get("player_count", 0) < 10:
        spots_needed = 10 - slot.get("player_count", 0)
        for i in range(spots_needed):
            register_guest(NORMAL_USER_USERNAME, f"ErrorTest_{i}_{random.randint(100,999)}")
            time.sleep(0.1)
    
    success_full, message_full, _ = register_guest(NORMAL_USER_USERNAME, f"Overflow_{random.randint(1000,9999)}")
    if not success_full:
        is_french_full = "complet" in message_full.lower()
        runner.run_test(test_name, lambda: is_french_full, True,
                       f"Message: {message_full}")
    else:
        runner.run_test(test_name, lambda: False, True, "Expected error did not occur")
    
    # Test 3: Authentication error is in French
    test_name = "Authentication error is in French"
    success_auth, message_auth, _ = register_player("fake_user_xyz", "Test")
    if not success_auth:
        is_french_auth = any(word in message_auth.lower() for word in ["authentification", "requis", "requise"])
        runner.run_test(test_name, lambda: is_french_auth, True,
                       f"Message: {message_auth}")
    else:
        runner.run_test(test_name, lambda: False, True, "Expected error did not occur")
    
    # Test 4: Permission error is informative
    test_name = "Permission error mentions inability to remove"
    # Ensure there's space in the slot
    slot_check = get_current_slot()
    if slot_check and slot_check.get("player_count", 0) >= 10:
        # Slot is full, remove one player to make space
        players = slot_check.get("players", [])
        if players:
            unregister_player(ADMIN_USERNAME, players[0])
            time.sleep(0.3)
    
    # Ensure user2 is actually registered and in the slot
    unregister_player(NORMAL_USER2_USERNAME, NORMAL_USER2_USERNAME)
    time.sleep(0.3)
    success_reg, msg_reg, _ = register_player(NORMAL_USER2_USERNAME, NORMAL_USER2_USERNAME)
    time.sleep(0.3)
    
    if success_reg:
        # Now try to remove as different user (should get permission error)
        success_perm, message_perm = unregister_player(NORMAL_USER_USERNAME, NORMAL_USER2_USERNAME)
        if not success_perm:
            is_informative = any(word in message_perm.lower() for word in ["supprimer", "permission", "pas", "trouvé"])
            runner.run_test(test_name, lambda: is_informative, True,
                           f"Message: {message_perm}")
        else:
            runner.run_test(test_name, lambda: False, True, "Expected error did not occur")
    else:
        runner.run_test(test_name, lambda: False, True, f"Could not register user: {msg_reg}")
    
    runner.print_summary()
    return runner


def test_rapid_operations():
    """Test system behavior under rapid successive operations"""
    print_test_header("RAPID OPERATIONS TESTS")
    runner = TestRunner("Rapid Operations")
    
    # Test 1: Rapid guest registrations
    test_name = "System handles rapid guest registrations"
    
    # Check if slot has space before attempting
    slot = get_current_slot()
    initial_count = slot.get("player_count", 0) if slot else 0
    has_space = initial_count < 10
    
    rapid_guests = []
    for i in range(3):
        guest_name = f"Rapid_{i}_{random.randint(1000,9999)}"
        success, _, _ = register_guest(NORMAL_USER_USERNAME, guest_name)
        rapid_guests.append(success)
        # No sleep - as fast as possible
    
    # If slot had space, expect registrations to succeed
    # If slot was full, expect registrations to fail (which is OK)
    if has_space:
        # At least some should succeed if there was space
        some_succeeded = sum(rapid_guests) > 0
        runner.run_test(test_name, lambda: some_succeeded, True,
                       f"Registered: {sum(rapid_guests)}/3 guests (had space: {has_space})")
    else:
        # Slot was full, so failures are expected and acceptable
        runner.run_test(test_name, lambda: True, True,
                       f"Slot was full ({initial_count}/10), registrations blocked as expected")
    
    # Test 2: Register then immediately unregister
    test_name = "Register and immediate unregister works"
    
    # Ensure slot has space
    slot = get_current_slot()
    if slot and slot.get("player_count", 0) >= 10:
        # Slot is full, remove one player to make space
        players = slot.get("players", [])
        if players:
            unregister_player(ADMIN_USERNAME, players[0])
            time.sleep(0.2)
    
    # Ensure user is not already registered
    unregister_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    time.sleep(0.2)
    
    success_reg, msg_reg, _ = register_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    time.sleep(0.1)  # Small delay between operations
    success_unreg, msg_unreg = unregister_player(NORMAL_USER_USERNAME, NORMAL_USER_USERNAME)
    
    both_succeeded = success_reg and success_unreg
    runner.run_test(test_name, lambda: both_succeeded, True,
                   f"Register: {success_reg}, Unregister: {success_unreg}")
    
    # Test 3: Multiple API calls to retrieve slot data
    test_name = "Multiple rapid slot retrievals return consistent data"
    slots = []
    for i in range(5):
        slot_data = get_current_slot()
        if slot_data:
            slots.append(slot_data.get("player_count", -1))
    
    all_same = len(set(slots)) == 1 if slots else False
    runner.run_test(test_name, lambda: all_same, True,
                   f"Counts: {slots}, All same: {all_same}")
    
    runner.print_summary()
    return runner


def test_special_characters_in_names():
    """Test handling of special characters in player and guest names"""
    print_test_header("SPECIAL CHARACTER HANDLING TESTS")
    runner = TestRunner("Special Character Handling")
    
    special_names = [
        ("Jean-François", "Hyphen and accent"),
        ("O'Brien", "Apostrophe"),
        ("José María", "Multiple accents with space"),
        ("李明", "Chinese characters"),
        ("Müller", "Umlaut"),
    ]
    
    for name, description in special_names:
        test_name = f"Guest name with {description}: '{name}'"
        guest_full_name = f"{name}_{random.randint(100,999)}"
        success, message, _ = register_guest(NORMAL_USER_USERNAME, guest_full_name)
        
        # Clean up if successful
        if success:
            time.sleep(0.2)
            slot = get_current_slot()
            if slot:
                players = slot.get("players", [])
                guest_entry = next((p for p in players if name in p), None)
                if guest_entry:
                    unregister_player(NORMAL_USER_USERNAME, guest_entry)
        
        runner.run_test(test_name, lambda s=success: s, True,
                       f"Accepted: {success}, Message: {message if not success else 'Success'}")
        time.sleep(0.2)
    
    runner.print_summary()
    return runner


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run all test suites"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 80)
    print("SOCCER SLOT MANAGER - COMPREHENSIVE API TEST SUITE".center(80))
    print("=" * 80)
    print(f"{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.YELLOW}Target URL: {BASE_URL}{Colors.RESET}")
    print(f"{Colors.YELLOW}Configuration: MAX_PLAYERS={MAX_PLAYERS}{Colors.RESET}")
    print(f"{Colors.YELLOW}Test Accounts:{Colors.RESET}")
    print(f"  {Colors.YELLOW}Admin: {ADMIN_USERNAME} (PIN: {'*' * len(ADMIN_PIN)}){Colors.RESET}")
    print(f"  {Colors.YELLOW}Normal User 1: {NORMAL_USER_USERNAME} (PIN: {'*' * len(NORMAL_USER_PIN)}){Colors.RESET}")
    print(f"  {Colors.YELLOW}Normal User 2: {NORMAL_USER2_USERNAME} (PIN: {'*' * len(NORMAL_USER2_PIN)}){Colors.RESET}\n")
    
    # Check server is running
    if not check_server_running():
        print(f"\n{Colors.RED}{Colors.BOLD}ERROR: Server is not running at {BASE_URL}{Colors.RESET}")
        print(f"{Colors.YELLOW}Please ensure the Docker container is running:{Colors.RESET}")
        print(f"  docker-compose up -d")
        print(f"  docker-compose ps\n")
        return
    
    print(f"{Colors.GREEN}✓ Server is running and responding{Colors.RESET}\n")
    
    # Verify test accounts exist
    print(f"{Colors.BOLD}Verifying test accounts...{Colors.RESET}")
    admin_valid, _ = login(ADMIN_USERNAME, ADMIN_PIN)
    user1_valid, _ = login(NORMAL_USER_USERNAME, NORMAL_USER_PIN)
    user2_valid, _ = login(NORMAL_USER2_USERNAME, NORMAL_USER2_PIN)
    
    print(f"  Admin account: {Colors.GREEN + '✓ Valid' if admin_valid else Colors.RED + '✗ Invalid'}{Colors.RESET}")
    print(f"  Normal User 1: {Colors.GREEN + '✓ Valid' if user1_valid else Colors.RED + '✗ Invalid'}{Colors.RESET}")
    print(f"  Normal User 2: {Colors.GREEN + '✓ Valid' if user2_valid else Colors.RED + '✗ Invalid'}{Colors.RESET}\n")
    
    if not (admin_valid and user1_valid and user2_valid):
        print(f"{Colors.RED}WARNING: Some test accounts are invalid. Some tests will fail.{Colors.RESET}")
        print(f"{Colors.YELLOW}Please create the test accounts or update credentials at the top of the script.{Colors.RESET}\n")
    
    # Run all test suites
    runners = []
    
    # Basic connectivity and structure tests
    print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 1: BASIC CONNECTIVITY & STRUCTURE ═══{Colors.RESET}")
    runners.append(test_server_connectivity())
    runners.append(test_slot_retrieval())
    runners.append(test_input_validation())
    runners.append(test_business_logic_via_api())
    runners.append(test_error_handling())
    
    # Authentication tests (no auth required)
    print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 2: AUTHENTICATION & AUTHORIZATION ═══{Colors.RESET}")
    runners.append(test_authentication())
    runners.append(test_registration_without_auth())
    
    # Normal user tests (requires valid normal user account)
    if user1_valid:
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 3: NORMAL USER FUNCTIONALITY ═══{Colors.RESET}")
        runners.append(test_normal_user_authentication())
        runners.append(test_normal_user_registration())
        runners.append(test_normal_user_guest_registration())
        runners.append(test_normal_user_unregistration())
        
        if user2_valid:
            runners.append(test_normal_user_cannot_remove_others())
    else:
        print(f"\n{Colors.YELLOW}⊘ Skipping normal user tests (invalid credentials){Colors.RESET}")
    
    # Admin user tests (requires valid admin account)
    if admin_valid:
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 4: ADMIN USER FUNCTIONALITY ═══{Colors.RESET}")
        runners.append(test_admin_authentication())
        runners.append(test_admin_registration())
        runners.append(test_admin_can_remove_any_player())
        runners.append(test_admin_guest_management())
    else:
        print(f"\n{Colors.YELLOW}⊘ Skipping admin tests (invalid credentials){Colors.RESET}")
    
    # Integration and journey tests
    if user1_valid and user2_valid:
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 5: INTEGRATION & USER JOURNEYS ═══{Colors.RESET}")
        runners.append(test_complete_user_journey())
        runners.append(test_multi_user_interactions())
    else:
        print(f"\n{Colors.YELLOW}⊘ Skipping integration tests (invalid credentials){Colors.RESET}")
    
    # Slot capacity tests (requires admin account to clear/fill slot)
    if admin_valid and user1_valid:
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 6: SLOT CAPACITY & FILLING TESTS ═══{Colors.RESET}")
        runners.append(test_progressive_slot_filling())
        runners.append(test_full_slot_behavior())
        runners.append(test_boundary_conditions())
    else:
        print(f"\n{Colors.YELLOW}⊘ Skipping slot capacity tests (requires admin + user accounts){Colors.RESET}")
    
    # Advanced tests (requires multiple user accounts)
    if admin_valid and user1_valid and user2_valid:
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 7: ADVANCED FUNCTIONALITY TESTS ═══{Colors.RESET}")
        runners.append(test_guest_permission_boundaries())
        runners.append(test_data_consistency())
        runners.append(test_error_message_quality())
        runners.append(test_rapid_operations())
        runners.append(test_timestamp_validation())
        runners.append(test_special_characters_in_names())
    else:
        print(f"\n{Colors.YELLOW}⊘ Skipping advanced tests (requires all test accounts){Colors.RESET}")
    
    # Calculate overall summary
    total_tests = sum(r.total for r in runners)
    total_passed = sum(r.passed for r in runners)
    all_failed_tests = []
    for r in runners:
        all_failed_tests.extend(r.failed_tests)
    
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
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed - review details below{Colors.RESET}\n")
        
        # Print detailed failed tests summary
        if all_failed_tests:
            print(f"{Colors.BOLD}{Colors.RED}{'='*80}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.RED}FAILED TESTS SUMMARY ({len(all_failed_tests)} failures){Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.RED}{'='*80}{Colors.RESET}\n")
            
            # Group by suite
            suite_failures = {}
            for failure in all_failed_tests:
                suite = failure.get('suite', 'Unknown')
                if suite not in suite_failures:
                    suite_failures[suite] = []
                suite_failures[suite].append(failure)
            
            for suite_name, failures in suite_failures.items():
                print(f"{Colors.BOLD}{Colors.YELLOW}[{suite_name}] - {len(failures)} failure(s){Colors.RESET}")
                for i, failure in enumerate(failures, 1):
                    print(f"  {Colors.RED}{i}.{Colors.RESET} {failure['name']}")
                    print(f"     {Colors.YELLOW}→ {failure['details']}{Colors.RESET}")
                print()
            
            print(f"{Colors.BOLD}{Colors.RED}{'='*80}{Colors.RESET}\n")
    
    # Cleanup: Clear all players from slot after tests
    if admin_valid:
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}CLEANUP - CLEARING SLOT{' '*59}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")
        
        slot = get_current_slot()
        if slot:
            players = slot.get("players", [])
            if players:
                print(f"{Colors.YELLOW}Removing {len(players)} player(s) from slot...{Colors.RESET}")
                removed_count = 0
                for player in players:
                    success, _ = unregister_player(ADMIN_USERNAME, player)
                    if success:
                        removed_count += 1
                    time.sleep(0.1)
                
                # Verify slot is empty
                final_slot = get_current_slot()
                final_count = final_slot.get("player_count", 0) if final_slot else -1
                
                if final_count == 0:
                    print(f"{Colors.GREEN}✓ Slot successfully cleared ({removed_count}/{len(players)} players removed){Colors.RESET}")
                else:
                    print(f"{Colors.YELLOW}⚠ Slot partially cleared ({removed_count}/{len(players)} players removed, {final_count} remaining){Colors.RESET}")
            else:
                print(f"{Colors.GREEN}✓ Slot is already empty{Colors.RESET}")
        else:
            print(f"{Colors.RED}✗ Could not retrieve slot for cleanup{Colors.RESET}")
        print()


if __name__ == "__main__":
    main()
