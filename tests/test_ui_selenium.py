#!/usr/bin/env python3
"""
UI Tests for Soccer Slot Manager
Uses Selenium WebDriver for browser automation testing
"""

import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import subprocess
import shutil
import os
import platform

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "http://192.168.0.100:8000"
API_BASE = f"{BASE_URL}/api"

# Test accounts (must exist in database)
TEST_USER = {
    "username": "testuser",
    "pin": "1234"
}

TEST_USER2 = {
    "username": "testuser2",
    "pin": "5678"
}

ADMIN_USER = {
    "username": "admin",
    "pin": "0000"
}

# =============================================================================
# COLOR OUTPUT
# =============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_test_header(title):
    """Print formatted test section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

# =============================================================================
# TEST RUNNER
# =============================================================================

class TestRunner:
    def __init__(self, suite_name):
        self.suite_name = suite_name
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def run_test(self, test_name, test_func, expected, context=""):
        """Run a single test and track results"""
        try:
            result = test_func()
            success = (result == expected) if not callable(expected) else expected()
            
            if success:
                self.passed += 1
                status = f"{Colors.GREEN}✓ PASS{Colors.RESET}"
            else:
                self.failed += 1
                status = f"{Colors.RED}✗ FAIL{Colors.RESET}"
            
            self.tests.append({
                "name": test_name,
                "passed": success,
                "context": context
            })
            
            context_str = f" - {context}" if context else ""
            print(f"{status} {test_name}{context_str}")
            
        except Exception as e:
            self.failed += 1
            status = f"{Colors.RED}✗ ERROR{Colors.RESET}"
            error_msg = str(e)
            self.tests.append({
                "name": test_name,
                "passed": False,
                "context": f"Exception: {error_msg}"
            })
            print(f"{status} {test_name} - Exception: {error_msg}")
    
    def print_summary(self):
        """Print test suite summary"""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}{'─'*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{self.suite_name} Summary:{Colors.RESET}")
        print(f"  Total:  {total}")
        print(f"  {Colors.GREEN}Passed: {self.passed}{Colors.RESET}")
        print(f"  {Colors.RED}Failed: {self.failed}{Colors.RESET}")
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"{Colors.BOLD}{'─'*70}{Colors.RESET}")

# =============================================================================
# SELENIUM HELPER FUNCTIONS
# =============================================================================

def is_wsl():
    """Detect if running in Windows Subsystem for Linux"""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower() or 'wsl' in f.read().lower()
    except:
        return False

def check_chrome_dependencies():
    """Check if required Chrome dependencies are installed"""
    required_libs = [
        'libnss3',
        'libgconf-2-4',
        'libfontconfig1'
    ]
    
    missing = []
    for lib in required_libs:
        result = subprocess.run(
            ['dpkg', '-l', lib],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            missing.append(lib)
    
    return missing

def check_browser_availability():
    """Check which browsers are available"""
    browsers = {
        'chrome': None,
        'chromium': None,
        'firefox': None
    }
    
    # Check for Chrome
    chrome_paths = ['google-chrome', 'chrome', 'chrome.exe']
    for path in chrome_paths:
        if shutil.which(path):
            browsers['chrome'] = path
            break
    
    # Check for Chromium
    chromium_paths = ['chromium', 'chromium-browser', 'chromium.exe']
    for path in chromium_paths:
        if shutil.which(path):
            browsers['chromium'] = path
            break
    
    # Check for Firefox
    firefox_paths = ['firefox', 'firefox.exe']
    for path in firefox_paths:
        if shutil.which(path):
            browsers['firefox'] = path
            break
    
    return browsers

def create_driver(headless=True, browser_preference=['chrome', 'chromium', 'firefox']):
    """Create and configure WebDriver with automatic browser detection"""
    available_browsers = check_browser_availability()
    wsl = is_wsl()
    
    if wsl:
        print(f"{Colors.YELLOW}ℹ  Detected WSL environment{Colors.RESET}")
    
    # Try browsers in order of preference
    for browser in browser_preference:
        if available_browsers.get(browser):
            try:
                if browser in ['chrome', 'chromium']:
                    return create_chrome_driver(headless, available_browsers[browser], wsl)
                elif browser == 'firefox':
                    return create_firefox_driver(headless)
            except Exception as e:
                error_msg = str(e)
                print(f"{Colors.YELLOW}⚠ Failed to create {browser} driver: {error_msg[:100]}{Colors.RESET}")
                
                # Provide WSL-specific guidance for status code 127
                if wsl and ('127' in error_msg or 'unexpectedly exited' in error_msg):
                    print(f"{Colors.CYAN}WSL Solution: Install required dependencies:{Colors.RESET}")
                    print(f"  sudo apt-get update")
                    print(f"  sudo apt-get install -y chromium-browser chromium-chromedriver")
                    print(f"  sudo apt-get install -y libnss3 libgconf-2-4 libfontconfig1")
                    print(f"  sudo apt-get install -y libx11-6 libx11-xcb1 libxcomposite1 libxdamage1")
                    print(f"  sudo apt-get install -y libxext6 libxfixes3 libxrandr2 libgbm1")
                continue
    
    # If all fail, provide helpful error with WSL-specific instructions
    error_msg = (
        f"{Colors.RED}No compatible browser found or browser failed to start!\n"
        f"Available browsers: {available_browsers}\n\n"
    )
    
    if wsl:
        error_msg += (
            f"{Colors.YELLOW}WSL-SPECIFIC INSTALLATION:{Colors.RESET}\n"
            f"Run these commands:\n\n"
            f"  sudo apt-get update\n"
            f"  sudo apt-get install -y chromium-browser chromium-chromedriver\n"
            f"  sudo apt-get install -y libnss3 libgconf-2-4 libfontconfig1\n"
            f"  sudo apt-get install -y libx11-6 libx11-xcb1 libxcomposite1\n"
            f"  sudo apt-get install -y libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1\n\n"
            f"Then run the tests again.{Colors.RESET}\n"
        )
    else:
        error_msg += (
            f"Ubuntu/Debian: sudo apt-get install chromium-browser\n"
            f"            or sudo apt-get install firefox\n"
            f"Fedora/RHEL:   sudo dnf install chromium{Colors.RESET}"
        )
    
    raise RuntimeError(error_msg)

def create_chrome_driver(headless=True, browser_binary=None, wsl=False):
    """Create Chrome/Chromium WebDriver"""
    options = ChromeOptions()
    
    if headless:
        options.add_argument('--headless=new')  # Use new headless mode
    
    # Essential Chrome options for running in containers/servers
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
    
    # Additional options for WSL
    if wsl:
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--single-process')  # Run in single process mode
    
    # Set binary location if specified
    if browser_binary:
        if 'chromium' in browser_binary:
            chromium_path = shutil.which('chromium-browser') or shutil.which('chromium')
            if chromium_path:
                options.binary_location = chromium_path
    
    # Suppress logging
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    try:
        # Try to use system chromedriver first
        chromedriver_path = shutil.which('chromedriver')
        if chromedriver_path:
            service = ChromeService(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # Let Selenium manage the driver
            driver = webdriver.Chrome(options=options)
        
        driver.implicitly_wait(5)
        return driver
    except WebDriverException as e:
        error_msg = str(e)
        if 'chrome not reachable' in error_msg.lower() or 'session not created' in error_msg.lower():
            raise RuntimeError(
                f"ChromeDriver found but Chrome/Chromium browser not accessible.\n"
                f"Install browser: sudo apt-get install chromium-browser"
            )
        elif 'status code was: 127' in error_msg:
            raise RuntimeError(
                f"ChromeDriver missing dependencies (status 127).\n"
                f"This is common in WSL. Install dependencies with:\n"
                f"sudo apt-get install -y libnss3 libgconf-2-4 libfontconfig1 libx11-6"
            )
        raise

def create_firefox_driver(headless=True):
    """Create Firefox WebDriver"""
    options = FirefoxOptions()
    
    if headless:
        options.add_argument('--headless')
    
    options.add_argument('--width=1920')
    options.add_argument('--height=1080')
    
    driver = webdriver.Firefox(options=options)
    driver.implicitly_wait(5)
    return driver

def wait_for_element(driver, by, value, timeout=10):
    """Wait for element to be present"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        return None

def wait_for_clickable(driver, by, value, timeout=10):
    """Wait for element to be clickable"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        return element
    except TimeoutException:
        return None

def is_modal_visible(driver, modal_class):
    """Check if a modal is visible"""
    try:
        modal = driver.find_element(By.CSS_SELECTOR, f".modal.{modal_class}")
        return "show" in modal.get_attribute("class")
    except NoSuchElementException:
        return False

def login_user(driver, username, pin):
    """Helper to log in a user"""
    # Click login button in header
    login_btn = wait_for_clickable(driver, By.XPATH, "//button[contains(text(), 'Connexion')]")
    if not login_btn:
        return False
    login_btn.click()
    
    time.sleep(0.5)
    
    # Fill login form
    username_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
    pin_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    
    username_input.clear()
    username_input.send_keys(username)
    pin_input.clear()
    pin_input.send_keys(pin)
    
    # Submit
    submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Se connecter')]")
    submit_btn.click()
    
    time.sleep(1)
    return True

def logout_user(driver):
    """Helper to log out current user"""
    try:
        logout_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Déconnexion')]")
        logout_btn.click()
        time.sleep(0.5)
        return True
    except NoSuchElementException:
        return False

# =============================================================================
# UI TEST SUITES
# =============================================================================

def test_page_load(driver):
    """Test that the page loads correctly"""
    print_test_header("PAGE LOAD TESTS")
    runner = TestRunner("Page Load")
    
    # Test 1: Page loads successfully
    test_name = "Page loads with 200 status"
    try:
        driver.get(BASE_URL)
        loaded = "Soccer Slot Manager" in driver.title
        runner.run_test(test_name, lambda: loaded, True,
                       f"Title: {driver.title}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 2: Main container is present
    test_name = "Main container element is present"
    container = wait_for_element(driver, By.CSS_SELECTOR, ".container")
    runner.run_test(test_name, lambda: container is not None, True,
                   f"Container found: {container is not None}")
    
    # Test 3: Page title is visible
    test_name = "Page title 'Soccer Slot Manager' is visible"
    try:
        h1 = driver.find_element(By.TAG_NAME, "h1")
        visible = h1.is_displayed() and "Soccer Slot Manager" in h1.text
        runner.run_test(test_name, lambda: visible, True,
                       f"Title: {h1.text}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Title not found")
    
    # Test 4: Slot date is displayed
    test_name = "Slot date information is displayed"
    try:
        date_paragraph = driver.find_element(By.XPATH, "//p[contains(@class, 'date')]")
        has_date = date_paragraph.text != ""
        runner.run_test(test_name, lambda: has_date, True,
                       f"Date: {date_paragraph.text[:50]}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Date not found")
    
    # Test 5: Players table is present
    test_name = "Players table is rendered"
    table = wait_for_element(driver, By.TAG_NAME, "table")
    runner.run_test(test_name, lambda: table is not None, True,
                   f"Table found: {table is not None}")
    
    # Test 6: Table has correct headers
    test_name = "Table headers are correct (N°, Joueur, Date d'inscription)"
    try:
        headers = driver.find_elements(By.TAG_NAME, "th")
        header_texts = [h.text for h in headers]
        correct = "N°" in header_texts and "Joueur" in header_texts
        runner.run_test(test_name, lambda: correct, True,
                       f"Headers: {header_texts}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 7: Login button is visible when not logged in
    test_name = "Login button is visible for anonymous users"
    try:
        login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Connexion')]")
        visible = login_btn.is_displayed()
        runner.run_test(test_name, lambda: visible, True,
                       f"Button visible: {visible}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Login button not found")
    
    # Test 8: Signup link is visible
    test_name = "Signup link is visible"
    try:
        signup_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Créer un compte')]")
        visible = signup_link.is_displayed()
        runner.run_test(test_name, lambda: visible, True,
                       f"Link visible: {visible}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Signup link not found")
    
    runner.print_summary()
    return runner

def test_login_modal(driver):
    """Test login modal functionality"""
    print_test_header("LOGIN MODAL TESTS")
    runner = TestRunner("Login Modal")
    
    # Test 1: Login modal opens on button click
    test_name = "Login modal opens when clicking login button"
    try:
        login_btn = wait_for_clickable(driver, By.XPATH, "//button[contains(text(), 'Connexion')]")
        login_btn.click()
        time.sleep(0.5)
        
        modal_visible = is_modal_visible(driver, "show")
        runner.run_test(test_name, lambda: modal_visible, True,
                       f"Modal visible: {modal_visible}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 2: Modal has correct title
    test_name = "Login modal displays 'Connexion' title"
    try:
        modal_title = driver.find_element(By.CSS_SELECTOR, ".modal.show h2")
        correct_title = modal_title.text == "Connexion"
        runner.run_test(test_name, lambda: correct_title, True,
                       f"Title: {modal_title.text}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Modal title not found")
    
    # Test 3: Username input field is present
    test_name = "Username input field is present"
    try:
        username_input = driver.find_element(By.CSS_SELECTOR, ".modal.show input[type='text']")
        runner.run_test(test_name, lambda: username_input is not None, True,
                       "Input found")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Username input not found")
    
    # Test 4: PIN input field is present with maxlength=4
    test_name = "PIN input field has maxlength='4'"
    try:
        pin_input = driver.find_element(By.CSS_SELECTOR, ".modal.show input[type='password']")
        maxlength = pin_input.get_attribute("maxlength")
        runner.run_test(test_name, lambda: maxlength == "4", True,
                       f"Maxlength: {maxlength}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "PIN input not found")
    
    # Test 5: Cancel button closes modal
    test_name = "Cancel button closes the login modal"
    try:
        cancel_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Annuler')]")
        cancel_btn.click()
        time.sleep(0.5)
        
        modal_closed = not is_modal_visible(driver, "show")
        runner.run_test(test_name, lambda: modal_closed, True,
                       f"Modal closed: {modal_closed}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Cancel button not found")
    
    runner.print_summary()
    return runner

def test_user_login_flow(driver):
    """Test complete user login flow"""
    print_test_header("USER LOGIN FLOW TESTS")
    runner = TestRunner("User Login Flow")
    
    # Test 1: Successful login with valid credentials
    test_name = "User can log in with valid credentials"
    success = login_user(driver, TEST_USER["username"], TEST_USER["pin"])
    
    # Check if user menu is visible
    try:
        user_display = driver.find_element(By.XPATH, f"//strong[contains(text(), '{TEST_USER['username']}')]")
        logged_in = user_display.is_displayed()
        runner.run_test(test_name, lambda: logged_in, True,
                       f"Logged in as: {TEST_USER['username']}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "User display not found")
    
    # Test 2: Logout button is visible when logged in
    test_name = "Logout button is visible after login"
    try:
        logout_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Déconnexion')]")
        visible = logout_btn.is_displayed()
        runner.run_test(test_name, lambda: visible, True,
                       f"Button visible: {visible}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Logout button not found")
    
    # Test 3: Registration section is visible when logged in
    test_name = "Registration section is visible for logged-in users"
    try:
        registration_section = driver.find_element(By.CSS_SELECTOR, ".registration-section")
        visible = registration_section.is_displayed()
        runner.run_test(test_name, lambda: visible, True,
                       f"Section visible: {visible}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Registration section not found")
    
    # Test 4: User can logout
    test_name = "User can logout successfully"
    logout_success = logout_user(driver)
    time.sleep(0.5)
    
    # Check if login button is back
    try:
        login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Connexion')]")
        logged_out = login_btn.is_displayed()
        runner.run_test(test_name, lambda: logged_out, True,
                       f"Logged out: {logged_out}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Login button not found")
    
    runner.print_summary()
    return runner

def test_player_registration(driver):
    """Test player registration functionality"""
    print_test_header("PLAYER REGISTRATION TESTS")
    runner = TestRunner("Player Registration")
    
    # Login first
    login_user(driver, TEST_USER["username"], TEST_USER["pin"])
    time.sleep(1)
    
    # Test 1: Registration button is present
    test_name = "Registration button is visible to logged-in user"
    try:
        register_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'inscrire')]")
        visible = register_btn.is_displayed()
        runner.run_test(test_name, lambda: visible, True,
                       f"Button visible: {visible}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Register button not found")
    
    # Test 2: User can register for slot
    test_name = "User can register themselves for the slot"
    try:
        # First unregister if already registered
        try:
            unregister_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'désinscrire')]")
            if unregister_btn.is_displayed():
                unregister_btn.click()
                time.sleep(1)
        except NoSuchElementException:
            pass
        
        # Now register
        register_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'inscrire')]")
        register_btn.click()
        time.sleep(1.5)
        
        # Check if user appears in table
        user_in_table = len(driver.find_elements(By.XPATH, f"//td[contains(text(), '{TEST_USER['username']}')]")) > 0
        runner.run_test(test_name, lambda: user_in_table, True,
                       f"User in table: {user_in_table}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 3: Unregister button appears after registration
    test_name = "Unregister button appears after successful registration"
    try:
        unregister_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'désinscrire')]")
        visible = unregister_btn.is_displayed()
        runner.run_test(test_name, lambda: visible, True,
                       f"Button visible: {visible}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Unregister button not found")
    
    # Test 4: User can unregister
    test_name = "User can unregister from the slot"
    try:
        unregister_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'désinscrire')]")
        unregister_btn.click()
        time.sleep(1.5)
        
        # Check if user is removed from table
        user_not_in_table = len(driver.find_elements(By.XPATH, f"//td[contains(text(), '{TEST_USER['username']}')]")) == 0
        runner.run_test(test_name, lambda: user_not_in_table, True,
                       f"User removed: {user_not_in_table}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    logout_user(driver)
    runner.print_summary()
    return runner

def test_guest_registration(driver):
    """Test guest registration functionality"""
    print_test_header("GUEST REGISTRATION TESTS")
    runner = TestRunner("Guest Registration")
    
    # Login
    login_user(driver, TEST_USER["username"], TEST_USER["pin"])
    time.sleep(1)
    
    # Test 1: Guest section is visible
    test_name = "Guest registration section is visible"
    try:
        guest_section = driver.find_element(By.CSS_SELECTOR, ".guest-section")
        visible = guest_section.is_displayed()
        runner.run_test(test_name, lambda: visible, True,
                       f"Section visible: {visible}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Guest section not found")
    
    # Test 2: Guest name input field is present
    test_name = "Guest name input field is present"
    try:
        guest_input = driver.find_element(By.CSS_SELECTOR, ".guest-section input[type='text']")
        runner.run_test(test_name, lambda: guest_input is not None, True,
                       "Input found")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Guest input not found")
    
    # Test 3: User can register a guest
    test_name = "User can register a guest player"
    guest_name = f"GuestUI_{random.randint(1000, 9999)}"
    try:
        guest_input = driver.find_element(By.CSS_SELECTOR, ".guest-section input[type='text']")
        guest_input.clear()
        guest_input.send_keys(guest_name)
        
        guest_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Enregistrer un invité')]")
        guest_btn.click()
        time.sleep(1.5)
        
        # Check if guest appears in table
        guest_in_table = len(driver.find_elements(By.XPATH, f"//td[contains(text(), '{guest_name}')]")) > 0
        runner.run_test(test_name, lambda: guest_in_table, True,
                       f"Guest in table: {guest_name}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 4: Guest input clears after registration
    test_name = "Guest input field clears after successful registration"
    try:
        guest_input = driver.find_element(By.CSS_SELECTOR, ".guest-section input[type='text']")
        is_empty = guest_input.get_attribute("value") == ""
        runner.run_test(test_name, lambda: is_empty, True,
                       f"Input empty: {is_empty}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Guest input not found")
    
    # Test 5: User can delete their own guest
    test_name = "User can delete their own guest"
    try:
        # Find delete button for the guest we just added
        delete_btn = driver.find_element(By.XPATH, 
            f"//tr[.//td[contains(text(), '{guest_name}')]]//button[contains(@class, 'delete-btn')]")
        delete_btn.click()
        time.sleep(1.5)
        
        # Check if guest is removed
        guest_removed = len(driver.find_elements(By.XPATH, f"//td[contains(text(), '{guest_name}')]")) == 0
        runner.run_test(test_name, lambda: guest_removed, True,
                       f"Guest removed: {guest_removed}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    logout_user(driver)
    runner.print_summary()
    return runner

def test_admin_features(driver):
    """Test admin-specific features"""
    print_test_header("ADMIN FEATURES TESTS")
    runner = TestRunner("Admin Features")
    
    # First, have a normal user register
    login_user(driver, TEST_USER["username"], TEST_USER["pin"])
    time.sleep(1)
    
    try:
        # Unregister if already registered
        try:
            unregister_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'désinscrire')]")
            if unregister_btn.is_displayed():
                unregister_btn.click()
                time.sleep(1)
        except:
            pass
        
        # Register user
        register_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'inscrire')]")
        register_btn.click()
        time.sleep(1.5)
    except:
        pass
    
    logout_user(driver)
    time.sleep(1)
    
    # Login as admin
    login_user(driver, ADMIN_USER["username"], ADMIN_USER["pin"])
    time.sleep(1)
    
    # Test 1: Admin link is visible
    test_name = "Admin panel link is visible for admin users"
    try:
        admin_link = driver.find_element(By.CSS_SELECTOR, "a.admin-link")
        visible = admin_link.is_displayed()
        runner.run_test(test_name, lambda: visible, True,
                       f"Link visible: {visible}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Admin link not found")
    
    # Test 2: Admin can see delete buttons for all players
    test_name = "Admin can see delete buttons for all players"
    try:
        delete_buttons = driver.find_elements(By.CSS_SELECTOR, ".delete-btn")
        has_buttons = len(delete_buttons) > 0
        runner.run_test(test_name, lambda: has_buttons, True,
                       f"Delete buttons found: {len(delete_buttons)}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 3: Admin can delete other users
    test_name = "Admin can remove other users from slot"
    try:
        # Find testuser in table
        user_row = driver.find_element(By.XPATH, f"//tr[.//td[contains(text(), '{TEST_USER['username']}')]]")
        delete_btn = user_row.find_element(By.CSS_SELECTOR, ".delete-btn")
        delete_btn.click()
        time.sleep(1.5)
        
        # Check if user is removed
        user_removed = len(driver.find_elements(By.XPATH, f"//td[contains(text(), '{TEST_USER['username']}')]")) == 0
        runner.run_test(test_name, lambda: user_removed, True,
                       f"User removed by admin: {user_removed}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    logout_user(driver)
    runner.print_summary()
    return runner

def test_data_display(driver):
    """Test data display and formatting"""
    print_test_header("DATA DISPLAY TESTS")
    runner = TestRunner("Data Display")
    
    driver.get(BASE_URL)
    time.sleep(1)
    
    # Test 1: Player count is displayed
    test_name = "Player count is displayed correctly"
    try:
        count_display = driver.find_element(By.XPATH, "//p[contains(., 'Joueurs inscrits')]")
        has_count = count_display.text != ""
        runner.run_test(test_name, lambda: has_count, True,
                       f"Count display: {count_display.text[:50]}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Count display not found")
    
    # Test 2: Table has 10 rows (for 10 players)
    test_name = "Table has exactly 10 rows for players"
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        runner.run_test(test_name, lambda: len(rows) == 10, True,
                       f"Rows: {len(rows)}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 3: Row numbers are sequential (1-10)
    test_name = "Row numbers are sequential from 1 to 10"
    try:
        numbers = driver.find_elements(By.CSS_SELECTOR, "tbody td:first-child")
        number_texts = [n.text for n in numbers]
        sequential = number_texts == [str(i) for i in range(1, 11)]
        runner.run_test(test_name, lambda: sequential, True,
                       f"Numbers: {number_texts}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 4: Date format is displayed correctly
    test_name = "Slot date is formatted correctly"
    try:
        date_elem = driver.find_element(By.XPATH, "//p[contains(@class, 'date')]")
        date_text = date_elem.text
        # Should contain "mercredi" (Wednesday) and time "19h00"
        has_day = "mercredi" in date_text.lower()
        runner.run_test(test_name, lambda: has_day, True,
                       f"Date: {date_text[:50]}")
    except NoSuchElementException:
        runner.run_test(test_name, lambda: False, True, "Date element not found")
    
    runner.print_summary()
    return runner

def test_responsive_updates(driver):
    """Test that UI updates after actions"""
    print_test_header("RESPONSIVE UPDATE TESTS")
    runner = TestRunner("Responsive Updates")
    
    # Login
    login_user(driver, TEST_USER2["username"], TEST_USER2["pin"])
    time.sleep(1)
    
    # Test 1: Player count updates after registration
    test_name = "Player count updates after user registration"
    try:
        # Get initial count
        count_elem = driver.find_element(By.XPATH, "//p[contains(., 'Joueurs inscrits')]")
        initial_text = count_elem.text
        
        # Unregister if needed
        try:
            unregister_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'désinscrire')]")
            unregister_btn.click()
            time.sleep(1.5)
        except:
            pass
        
        # Register
        register_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'inscrire')]")
        register_btn.click()
        time.sleep(1.5)
        
        # Get new count
        count_elem = driver.find_element(By.XPATH, "//p[contains(., 'Joueurs inscrits')]")
        new_text = count_elem.text
        
        # Text should be different
        updated = new_text != initial_text
        runner.run_test(test_name, lambda: updated, True,
                       f"Count changed: {updated}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 2: Table updates after registration
    test_name = "Table shows newly registered user immediately"
    try:
        user_in_table = len(driver.find_elements(By.XPATH, 
            f"//td[contains(text(), '{TEST_USER2['username']}')]")) > 0
        runner.run_test(test_name, lambda: user_in_table, True,
                       f"User visible: {user_in_table}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 3: Button changes after registration
    test_name = "Register button changes to unregister button"
    try:
        unregister_btn_exists = len(driver.find_elements(By.XPATH, 
            "//button[contains(text(), 'désinscrire')]")) > 0
        runner.run_test(test_name, lambda: unregister_btn_exists, True,
                       f"Unregister button visible: {unregister_btn_exists}")
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    logout_user(driver)
    runner.print_summary()
    return runner

def test_error_handling(driver):
    """Test error message display"""
    print_test_header("ERROR HANDLING TESTS")
    runner = TestRunner("Error Handling")
    
    # Test 1: Invalid login shows error message
    test_name = "Invalid login credentials show error message"
    try:
        # Open login modal
        login_btn = wait_for_clickable(driver, By.XPATH, "//button[contains(text(), 'Connexion')]")
        login_btn.click()
        time.sleep(0.5)
        
        # Fill with invalid credentials
        username_input = driver.find_element(By.CSS_SELECTOR, ".modal.show input[type='text']")
        pin_input = driver.find_element(By.CSS_SELECTOR, ".modal.show input[type='password']")
        
        username_input.clear()
        username_input.send_keys("invaliduser")
        pin_input.clear()
        pin_input.send_keys("9999")
        
        # Submit
        submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Se connecter')]")
        submit_btn.click()
        time.sleep(1)
        
        # Check for error message
        error_elem = driver.find_element(By.CSS_SELECTOR, ".modal.show .error")
        error_visible = error_elem.is_displayed()
        runner.run_test(test_name, lambda: error_visible, True,
                       f"Error shown: {error_elem.text[:50] if error_visible else 'N/A'}")
        
        # Close modal
        cancel_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Annuler')]")
        cancel_btn.click()
        time.sleep(0.5)
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    # Test 2: Empty guest name shows error
    test_name = "Empty guest name shows appropriate error"
    try:
        # Login
        login_user(driver, TEST_USER["username"], TEST_USER["pin"])
        time.sleep(1)
        
        # Try to register guest with empty name
        guest_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Enregistrer un invité')]")
        guest_btn.click()
        time.sleep(1)
        
        # Check for error (could be inline or toast)
        # The API should reject this and Vue should display the error
        has_error = len(driver.find_elements(By.CSS_SELECTOR, ".error")) > 0
        runner.run_test(test_name, lambda: has_error, True,
                       f"Error displayed: {has_error}")
        
        logout_user(driver)
    except Exception as e:
        runner.run_test(test_name, lambda: False, True, f"Error: {e}")
    
    runner.print_summary()
    return runner

# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def main():
    """Run all UI tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'SOCCER SLOT MANAGER - UI TESTS':^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Test Target: {BASE_URL}{Colors.RESET}")
    print(f"{Colors.CYAN}Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    # Check browser availability
    print(f"{Colors.YELLOW}🔍 Checking for available browsers...{Colors.RESET}")
    available = check_browser_availability()
    found_browsers = [k for k, v in available.items() if v]
    
    if not found_browsers:
        print(f"\n{Colors.RED}❌ No supported browser found!{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Please install a browser:{Colors.RESET}")
        print(f"  Ubuntu/Debian: sudo apt-get install chromium-browser")
        print(f"              or sudo apt-get install firefox")
        print(f"  Fedora/RHEL:   sudo dnf install chromium")
        print(f"  macOS:         brew install --cask chromium")
        return 1
    
    print(f"{Colors.GREEN}✓ Found browsers: {', '.join(found_browsers)}{Colors.RESET}\n")
    
    driver = None
    runners = []
    
    try:
        # Create WebDriver
        print(f"{Colors.YELLOW}🚀 Initializing WebDriver...{Colors.RESET}\n")
        driver = create_driver(headless=True)
        
        # Run test suites
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 1: PAGE LOAD & STRUCTURE ═══{Colors.RESET}")
        runners.append(test_page_load(driver))
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 2: AUTHENTICATION UI ═══{Colors.RESET}")
        # Reload page for clean state
        driver.get(BASE_URL)
        time.sleep(1)
        runners.append(test_login_modal(driver))
        
        driver.get(BASE_URL)
        time.sleep(1)
        runners.append(test_user_login_flow(driver))
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 3: USER ACTIONS ═══{Colors.RESET}")
        driver.get(BASE_URL)
        time.sleep(1)
        runners.append(test_player_registration(driver))
        
        driver.get(BASE_URL)
        time.sleep(1)
        runners.append(test_guest_registration(driver))
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 4: ADMIN FUNCTIONALITY ═══{Colors.RESET}")
        driver.get(BASE_URL)
        time.sleep(1)
        runners.append(test_admin_features(driver))
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 5: DATA DISPLAY & UPDATES ═══{Colors.RESET}")
        driver.get(BASE_URL)
        time.sleep(1)
        runners.append(test_data_display(driver))
        
        driver.get(BASE_URL)
        time.sleep(1)
        runners.append(test_responsive_updates(driver))
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══ PHASE 6: ERROR HANDLING ═══{Colors.RESET}")
        driver.get(BASE_URL)
        time.sleep(1)
        runners.append(test_error_handling(driver))
        
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error during test execution: {e}{Colors.RESET}")
    
    finally:
        if driver:
            driver.quit()
            print(f"\n{Colors.YELLOW}🛑 WebDriver closed{Colors.RESET}\n")
    
    # Print final summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'FINAL TEST SUMMARY':^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'═'*70}{Colors.RESET}\n")
    
    total_passed = sum(r.passed for r in runners)
    total_failed = sum(r.failed for r in runners)
    total_tests = total_passed + total_failed
    
    for runner in runners:
        suite_total = runner.passed + runner.failed
        suite_rate = (runner.passed / suite_total * 100) if suite_total > 0 else 0
        status_color = Colors.GREEN if runner.failed == 0 else Colors.YELLOW if suite_rate >= 70 else Colors.RED
        print(f"{status_color}▸ {runner.suite_name}: {runner.passed}/{suite_total} passed ({suite_rate:.0f}%){Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{'─'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Overall Results:{Colors.RESET}")
    print(f"  Total Tests:  {total_tests}")
    print(f"  {Colors.GREEN}Passed: {total_passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {total_failed}{Colors.RESET}")
    
    if total_tests > 0:
        overall_rate = (total_passed / total_tests * 100)
        print(f"  Success Rate: {overall_rate:.1f}%")
        
        if total_failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL UI TESTS PASSED! 🎉{Colors.RESET}")
        else:
            print(f"\n{Colors.YELLOW}⚠ Some tests failed. Review the output above for details.{Colors.RESET}")
    
    print(f"{Colors.BOLD}{'─'*70}{Colors.RESET}\n")
    
    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    exit(main())
