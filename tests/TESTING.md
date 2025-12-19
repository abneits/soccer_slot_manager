# Testing Documentation

## Overview

The Soccer Slot Manager has comprehensive test coverage for both **API** and **UI** functionality:

- **API Tests**: `test_api_endpoints.py` - Black-box HTTP endpoint testing (220+ tests)
- **UI Tests**: `test_ui_selenium.py` - Browser automation testing with Selenium (50+ tests)

## Prerequisites

### For API Tests

```bash
pip install requests
```

### For UI Tests

```bash
pip install selenium
```

You also need **ChromeDriver** installed:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y chromium-chromedriver
```

**macOS:**
```bash
brew install chromedriver
```

**Or download manually from:** https://chromedriver.chromium.org/

## Test Accounts

Both test suites require these accounts to exist in your database:

| Username | PIN | Role |
|----------|-----|------|
| `admin` | `0000` | Administrator |
| `testuser` | `1234` | Normal user |
| `testuser2` | `5678` | Normal user |

## Running API Tests

### Full Test Suite

```bash
python test_api_endpoints.py
```

### Test Coverage

The API test suite covers **7 phases** with 220+ tests:

1. **Basic Connectivity** (11 tests)
   - Health check endpoint
   - API availability
   - Response format validation

2. **Slot Retrieval** (14 tests)
   - GET /api/current-slot
   - Date/time validation (Wednesday at 19:00)
   - Field structure and types

3. **Authentication** (12 tests)
   - Login/signup/PIN change
   - Invalid credentials
   - Authorization checks

4. **Normal User Operations** (25 tests)
   - Self-registration/unregistration
   - Guest management
   - Permission boundaries

5. **Admin Operations** (18 tests)
   - Remove any player
   - Admin-only actions
   - Permission validation

6. **Slot Capacity** (35+ tests)
   - Progressive filling (0→10)
   - Full slot behavior
   - Boundary conditions

7. **Advanced Tests** (100+ tests)
   - Integration scenarios
   - Data consistency
   - Error messages
   - Rapid operations
   - Special characters
   - Timestamp validation
   - Guest permissions

### Expected Output

```
╔══════════════════════════════════════════════════════════════════╗
║              SOCCER SLOT MANAGER - API TESTS                     ║
╚══════════════════════════════════════════════════════════════════╝

═══ PHASE 1: BASIC CONNECTIVITY TESTS ═══
✓ PASS Health endpoint is accessible
✓ PASS Health returns 200 status code
...

FINAL TEST SUMMARY
═══════════════════════════════════════════════════════════════════
▸ Basic Connectivity: 11/11 passed (100%)
▸ Slot Retrieval: 14/14 passed (100%)
...
Overall Success Rate: 100%
✓ ALL API TESTS PASSED! 🎉
```

## Running UI Tests

### Full Test Suite

```bash
python test_ui_selenium.py
```

### Test Coverage

The UI test suite covers **6 phases** with 50+ tests:

1. **Page Load & Structure** (8 tests)
   - Page loads correctly
   - Main elements present (title, table, buttons)
   - Table headers correct

2. **Authentication UI** (9 tests)
   - Login modal opens/closes
   - Form fields present
   - Login/logout flow

3. **User Actions** (9 tests)
   - User registration/unregistration
   - Button state changes
   - Table updates

4. **Guest Registration** (5 tests)
   - Guest section visible
   - Register/delete guests
   - Input clearing

5. **Admin Functionality** (3 tests)
   - Admin panel link
   - Delete buttons for all players
   - Remove other users

6. **Data Display & Updates** (10 tests)
   - Player count display
   - Table formatting (10 rows, sequential numbers)
   - Real-time updates after actions

7. **Error Handling** (2 tests)
   - Invalid login error display
   - Empty field validation

### Headless vs Visual Mode

By default, tests run in **headless mode** (no browser window). To see the browser:

Edit `test_ui_selenium.py`:
```python
driver = create_driver(headless=False)  # Change to False
```

### Expected Output

```
═══════════════════════════════════════════════════════════════════
           SOCCER SLOT MANAGER - UI TESTS
═══════════════════════════════════════════════════════════════════

🚀 Initializing Chrome WebDriver...

═══ PHASE 1: PAGE LOAD & STRUCTURE ═══
✓ PASS Page loads with 200 status
✓ PASS Main container element is present
...

FINAL TEST SUMMARY
═══════════════════════════════════════════════════════════════════
▸ Page Load: 8/8 passed (100%)
▸ Login Modal: 5/5 passed (100%)
...
Overall Success Rate: 100%
✓ ALL UI TESTS PASSED! 🎉
```

## Troubleshooting

### API Tests Failing

**Issue**: Connection refused errors
```
Solution: Ensure the server is running at http://192.168.0.100:8000
```

**Issue**: Authentication tests fail
```
Solution: Verify test accounts exist with correct PINs in the database
```

**Issue**: Slot is full, tests fail
```
Solution: Run as admin to clear slot, or wait for next Wednesday reset
```

### UI Tests Failing

**Issue**: ChromeDriver not found
```
Solution: Install ChromeDriver and ensure it's in your PATH
```

**Issue**: Elements not found
```
Solution: The page may be loading slowly. Increase timeouts in wait_for_element()
```

**Issue**: Tests pass but browser crashes
```
Solution: Add more memory to Docker container or run in headless mode
```

## Configuration

### Change Test Target URL

Edit the configuration section in each test file:

**API Tests:**
```python
BASE_URL = "http://192.168.0.100:8000"
API_BASE = f"{BASE_URL}/api"
```

**UI Tests:**
```python
BASE_URL = "http://192.168.0.100:8000"
```

### Change Test Accounts

Update the credentials in each test file:

```python
TEST_USER = {
    "username": "testuser",
    "pin": "1234"
}
```

## Best Practices

### Before Running Tests

1. **Backup your data** (tests modify the slot)
2. **Ensure server is running** and accessible
3. **Verify test accounts exist** with correct credentials
4. **Check slot state** - some tests require specific conditions

### During Test Development

1. **Run tests frequently** to catch regressions early
2. **Use verbose output** to understand failures
3. **Test in isolation** when debugging specific features
4. **Clean up test data** between runs if needed

### After Tests Complete

- Review any failures carefully
- Check server logs for backend errors
- Verify database state is consistent
- Run tests again to confirm fixes

## Continuous Integration

To run tests in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run API Tests
  run: python test_api_endpoints.py

- name: Run UI Tests
  run: |
    sudo apt-get install chromium-chromedriver
    python test_ui_selenium.py
```

## Test Data Cleanup

Both test suites clean up after themselves, but you can manually clean the slot:

```bash
# Using API
curl -X POST "http://192.168.0.100:8000/api/unregister?username=admin" \
  -H "Content-Type: application/json" \
  -d '{"name": "testuser"}'
```

Or login as admin and use the UI to clear all players.

## Coverage Statistics

| Test Suite | Tests | Lines | Coverage |
|------------|-------|-------|----------|
| API Tests | 220+ | 2003 | Full API |
| UI Tests | 50+ | 1000+ | Full UI |
| **Total** | **270+** | **3000+** | **End-to-End** |

## Support

For issues or questions about testing:
1. Check troubleshooting section above
2. Review test output carefully
3. Verify server logs for backend errors
4. Ensure all prerequisites are installed
