# Testing Guide - Members History Project

**Last Updated:** November 10, 2025

This document provides a consolidated reference for testing approaches and patterns used across the Members History project.

---

## Table of Contents

1. [Test Architecture](#test-architecture)
2. [Backend Testing](#backend-testing)
3. [Frontend Testing](#frontend-testing)
4. [Manual Testing Patterns](#manual-testing-patterns)
5. [Common Testing Scenarios](#common-testing-scenarios)
6. [Troubleshooting](#troubleshooting)

---

## Test Architecture

### Project Structure

```
members-history/
├── backend/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Pytest fixtures and configuration
│   │   ├── mock_data.py         # Sample data for testing
│   │   ├── test_determine_shift_type.py
│   │   └── test_member_history_api.py
│   ├── app.py                   # Flask application
│   ├── odoo_client.py           # Odoo integration
│   ├── pytest.ini               # Pytest configuration
│   └── requirements-dev.txt     # Development dependencies
│
├── frontend/
│   ├── src/
│   │   ├── tests/
│   │   │   ├── setup.js         # Vitest configuration
│   │   │   ├── getEventTitle.test.jsx
│   │   │   └── ShiftDisplay.test.jsx
│   │   ├── App.jsx
│   │   └── i18n.js
│   ├── vitest.config.js         # Vitest configuration
│   └── package.json
│
└── docs/
    └── agent/
        └── testing/
            ├── testing-guide.md (this file)
            └── YYYY-MM-DD-feature-validation.md
```

### Testing Philosophy

- **Unit Tests:** Test individual functions in isolation
- **Integration Tests:** Test how components work together
- **Component Tests:** Test React component rendering and behavior
- **Manual Tests:** Verify user-facing features and edge cases

---

## Backend Testing

### Setup

**Install dependencies:**
```bash
cd backend
pip install -r requirements-dev.txt
```

**Dependencies:**
- `pytest==7.4.3` - Test framework
- `pytest-cov==4.1.0` - Coverage reporting
- `pytest-mock==3.12.0` - Mocking utilities
- `pytest-flask==1.3.0` - Flask testing utilities

### Running Tests

**All tests:**
```bash
pytest -v
```

**With coverage:**
```bash
pytest --cov=. --cov-report=html
```

**Specific test file:**
```bash
pytest tests/test_determine_shift_type.py -v
```

**Specific test:**
```bash
pytest tests/test_determine_shift_type.py::TestDetermineShiftType::test_shift_with_ftop_counter_event -v
```

**Tests matching pattern:**
```bash
pytest -k "ftop" -v
```

### Test Structure

#### Fixtures (conftest.py)

Fixtures provide reusable test data and setup:

```python
@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()

@pytest.fixture
def mock_odoo_client(mocker):
    """Create a mock OdooClient for testing."""
    mock = mocker.MagicMock(spec=OdooClient)
    return mock

@pytest.fixture
def sample_shift_with_ftop_counter():
    """Sample shift registration with FTOP counter event."""
    return {
        'id': 101,
        'shift_id': [201, 'FTOP Wednesday 09:00'],
        'shift_type_id': [1, 'FTOP'],
        # ... more fields
    }
```

**Usage in tests:**
```python
def test_something(client, mock_odoo_client, sample_shift_with_ftop_counter):
    # Fixtures are automatically injected
    response = client.get('/api/health')
    assert response.status_code == 200
```

#### Unit Tests

Test individual functions with various inputs:

```python
def test_shift_with_ftop_counter_event(self, sample_shift_with_ftop_counter):
    from app import determine_shift_type
    
    shift = sample_shift_with_ftop_counter
    shift_id = shift['shift_id'][0]
    shift_counter_map = {shift_id: {'type': 'ftop'}}
    
    shift_type, shift_type_id = determine_shift_type(shift, shift_counter_map, shift_id)
    
    assert shift_type == 'ftop'
```

**Pattern:**
1. Arrange: Set up test data
2. Act: Call the function
3. Assert: Verify the result

#### Integration Tests

Test API endpoints with mocked Odoo client:

```python
def test_ftop_member_with_mixed_shift_types(self, client, mock_odoo_client, mocker):
    # Setup mock data
    mock_odoo_client.get_member_shift_history.return_value = mock_shifts
    mock_odoo_client.get_member_counter_events.return_value = mock_counter_events
    mocker.patch('app.odoo', mock_odoo_client)
    
    # Make request
    response = client.get('/api/member/123/history')
    
    # Verify response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['events']) == 2
```

**Pattern:**
1. Mock external dependencies
2. Make API request
3. Verify response structure and data

### Coverage Goals

- **Core logic:** 100% coverage (e.g., `determine_shift_type()`)
- **API endpoints:** 100% coverage
- **Overall:** 70%+ coverage (excluding error paths and external calls)

**View coverage report:**
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

---

## Frontend Testing

### Setup

**Install dependencies:**
```bash
cd frontend
npm install --legacy-peer-deps
```

**Key dependencies:**
- `vitest` - Test framework (Vite-native)
- `@testing-library/react` - React testing utilities
- `@testing-library/jest-dom` - DOM matchers

### Running Tests

**All tests:**
```bash
npm test -- --run
```

**Watch mode (for development):**
```bash
npm test
```

**With coverage:**
```bash
npm run test:coverage
```

**Specific test file:**
```bash
npm test -- src/tests/getEventTitle.test.jsx --run
```

**Tests matching pattern:**
```bash
npm test -- --grep "FTOP" --run
```

### Test Structure

#### Unit Tests (getEventTitle.test.jsx)

Test pure functions with various inputs:

```javascript
describe('getEventTitle', () => {
  describe('FTOP shifts', () => {
    it('returns ftopShiftAttended for attended FTOP shift', () => {
      const event = {
        type: 'shift',
        shift_type: 'ftop',
        state: 'done'
      }
      
      const result = getEventTitle(event, mockT)
      
      expect(result).toBe('FTOP Shift Attended')
    })
  })
})
```

**Pattern:**
1. Describe the function/feature
2. Group related tests
3. Test each case with clear assertions

#### Component Tests (ShiftDisplay.test.jsx)

Test React component rendering:

```javascript
describe('ShiftEvent Display', () => {
  describe('Unknown shift type warning', () => {
    it('displays warning badge for unknown shift type', () => {
      const event = {
        type: 'shift',
        shift_type: 'unknown',
        state: 'done'
      }
      
      render(<ShiftEvent event={event} />)
      
      const warning = screen.getByTestId('unknown-type-warning')
      expect(warning).toBeInTheDocument()
      expect(warning).toHaveTextContent('⚠️')
    })
  })
})
```

**Pattern:**
1. Render component with test props
2. Query for elements using `screen`
3. Assert element presence and content

### Testing Best Practices

**Use data-testid for queries:**
```javascript
// Good
const badge = screen.getByTestId('ftop-indicator')

// Avoid
const badge = screen.getByText('FTOP')  // Too fragile
```

**Test user interactions:**
```javascript
import { userEvent } from '@testing-library/user-event'

it('switches language on button click', async () => {
  render(<App />)
  const button = screen.getByRole('button', { name: /français/i })
  await userEvent.click(button)
  expect(screen.getByText('Français')).toBeInTheDocument()
})
```

**Mock translations:**
```javascript
const mockT = (key) => {
  const translations = {
    'timeline.ftopShiftAttended': 'FTOP Shift Attended',
    // ...
  }
  return translations[key] || key
}
```

---

## Manual Testing Patterns

### Pattern 1: Feature Verification

**Purpose:** Verify a feature works end-to-end

**Steps:**
1. Start both servers
2. Navigate to feature
3. Perform key actions
4. Verify expected outcomes
5. Check for errors

**Example:**
```
Feature: FTOP Shift Display
1. Search for FTOP member
2. View their history
3. Verify FTOP shifts have blue badge
4. Verify standard shifts don't have badge
5. Check console for errors
```

### Pattern 2: Edge Case Testing

**Purpose:** Verify edge cases are handled gracefully

**Steps:**
1. Identify edge case scenario
2. Set up test data
3. Perform action
4. Verify graceful handling
5. Check for error messages

**Example:**
```
Edge Case: Missing shift_type_id
1. Find shift without shift_type_id
2. View in timeline
3. Verify warning badge appears
4. Verify shift still displays
5. Check no console errors
```

### Pattern 3: Error Scenario Testing

**Purpose:** Verify error handling

**Steps:**
1. Trigger error condition
2. Observe error handling
3. Verify user-friendly message
4. Verify application stability
5. Verify recovery path

**Example:**
```
Error: API Connection Failure
1. Stop backend server
2. Try to load member history
3. Verify error message appears
4. Verify page doesn't crash
5. Restart backend and retry
```

### Pattern 4: Cross-Browser Testing

**Purpose:** Verify feature works across browsers

**Steps:**
1. Open feature in Chrome
2. Verify all functionality
3. Open in Firefox
4. Verify all functionality
5. Open in Safari
6. Verify all functionality

**Checklist:**
- [ ] Layout looks correct
- [ ] Styling is consistent
- [ ] Icons render properly
- [ ] Interactions work smoothly
- [ ] No console errors

### Pattern 5: Accessibility Testing

**Purpose:** Verify feature is accessible

**Steps:**
1. Use keyboard only (no mouse)
2. Verify all controls are reachable
3. Check color contrast
4. Verify text labels on icons
5. Test with screen reader (if applicable)

**Checklist:**
- [ ] All buttons are keyboard accessible
- [ ] Focus indicators are visible
- [ ] Color contrast meets WCAG standards
- [ ] Icons have text labels
- [ ] Form fields have labels

---

## Common Testing Scenarios

### Scenario 1: Testing Shift Type Determination

**What to test:**
- FTOP shifts are correctly identified
- Standard shifts are correctly identified
- Unknown shifts are handled
- Counter type takes precedence

**Test data needed:**
```python
# FTOP shift with counter
shift = {
    'shift_id': [101, 'FTOP Wed'],
    'shift_type_id': [1, 'FTOP']
}
counter_map = {
    101: {'type': 'ftop'}
}

# Standard shift with counter
shift = {
    'shift_id': [102, 'Mon'],
    'shift_type_id': [2, 'Standard']
}
counter_map = {
    102: {'type': 'standard'}
}

# Unknown shift
shift = {
    'shift_id': [103, 'Unknown']
    # No shift_type_id
}
counter_map = {}
```

**Test code:**
```python
def test_shift_types(shift, counter_map, shift_id, expected_type):
    from app import determine_shift_type
    shift_type, _ = determine_shift_type(shift, counter_map, shift_id)
    assert shift_type == expected_type
```

### Scenario 2: Testing Counter Aggregation

**What to test:**
- Counter events are aggregated correctly
- Running totals are calculated
- FTOP and Standard counters are separate
- Chronological ordering is maintained

**Test data needed:**
```python
counter_events = [
    {
        'shift_id': [101, 'FTOP'],
        'type': 'ftop',
        'point_qty': 1,
        'create_date': '2025-01-15'
    },
    {
        'shift_id': [102, 'Standard'],
        'type': 'standard',
        'point_qty': 1,
        'create_date': '2025-01-20'
    }
]
```

**Verification:**
- [ ] FTOP total: 1
- [ ] Standard total: 1
- [ ] Events sorted chronologically
- [ ] No double-counting

### Scenario 3: Testing Translation System

**What to test:**
- All shift types are translatable
- Language switching works
- No missing translation keys
- Translations are accurate

**Test data needed:**
```javascript
const translations = {
  en: {
    'timeline.ftopShiftAttended': 'FTOP Shift Attended',
    'timeline.shiftAttended': 'Shift Attended'
  },
  fr: {
    'timeline.ftopShiftAttended': 'Service Volant Effectué',
    'timeline.shiftAttended': 'Service Effectué'
  }
}
```

**Verification:**
- [ ] English text displays in EN mode
- [ ] French text displays in FR mode
- [ ] No untranslated keys visible
- [ ] Language switch is immediate

---

## Troubleshooting

### Backend Issues

**Problem:** Tests fail with "ModuleNotFoundError: No module named 'pytest'"

**Solution:**
```bash
cd backend
pip install -r requirements-dev.txt
```

**Problem:** Tests fail with "Cannot import app"

**Solution:**
```bash
# Make sure you're in the backend directory
cd backend
pytest -v
```

**Problem:** Mock Odoo client not working

**Solution:**
```python
# Use mocker fixture to patch
mocker.patch('app.odoo', mock_odoo_client)

# Or use the mock directly in tests
mock_odoo_client.get_member_shift_history.return_value = mock_shifts
```

### Frontend Issues

**Problem:** Tests fail with "Cannot find module '@testing-library/react'"

**Solution:**
```bash
cd frontend
npm install --legacy-peer-deps
```

**Problem:** Tests hang or timeout

**Solution:**
```bash
# Use --run flag to exit after tests complete
npm test -- --run

# Or set timeout in vitest.config.js
export default {
  test: {
    testTimeout: 10000
  }
}
```

**Problem:** Translation tests fail

**Solution:**
```javascript
// Mock the translation function
const mockT = (key) => {
  const translations = {
    'timeline.ftopShiftAttended': 'FTOP Shift Attended'
  }
  return translations[key] || key
}

// Use in test
const result = getEventTitle(event, mockT)
```

### Common Issues

**Problem:** API tests fail with "Connection refused"

**Solution:**
```bash
# Make sure backend is running
cd backend
python app.py

# Or mock the Odoo client
mocker.patch('app.odoo', mock_odoo_client)
```

**Problem:** Coverage report shows 0% for some files

**Solution:**
```bash
# Exclude test files from coverage
pytest --cov=. --cov-report=html --cov-report=term-missing
```

**Problem:** Tests pass locally but fail in CI

**Solution:**
- Check Python/Node version matches
- Ensure all dependencies are installed
- Check environment variables are set
- Verify test data is available

---

## Best Practices

### Backend Testing

1. **Use fixtures for reusable data**
   ```python
   @pytest.fixture
   def sample_shift():
       return {...}
   ```

2. **Mock external dependencies**
   ```python
   mocker.patch('app.odoo', mock_odoo_client)
   ```

3. **Test both happy path and edge cases**
   ```python
   # Happy path
   def test_valid_shift_type():
       assert determine_shift_type(...) == 'ftop'
   
   # Edge case
   def test_unknown_shift_type():
       assert determine_shift_type(...) == 'unknown'
   ```

4. **Use descriptive test names**
   ```python
   # Good
   def test_shift_with_ftop_counter_event_returns_ftop_type():
   
   # Avoid
   def test_shift():
   ```

### Frontend Testing

1. **Use data-testid for queries**
   ```javascript
   <div data-testid="ftop-indicator">FTOP</div>
   const badge = screen.getByTestId('ftop-indicator')
   ```

2. **Test behavior, not implementation**
   ```javascript
   // Good - tests what user sees
   expect(screen.getByText('FTOP Shift Attended')).toBeInTheDocument()
   
   // Avoid - tests implementation details
   expect(component.state.shiftType).toBe('ftop')
   ```

3. **Mock translations consistently**
   ```javascript
   const mockT = (key) => translations[key] || key
   ```

4. **Test accessibility**
   ```javascript
   const button = screen.getByRole('button', { name: /submit/i })
   ```

### General

1. **Keep tests focused and independent**
   - One test per behavior
   - No dependencies between tests
   - Use fixtures for setup

2. **Use clear assertions**
   ```python
   # Good
   assert shift_type == 'ftop', "Shift with FTOP counter should return 'ftop'"
   
   # Avoid
   assert shift_type == 'ftop'
   ```

3. **Document complex test scenarios**
   ```python
   def test_counter_precedence_over_shift_type_id(self):
       """
       Test that counter event type takes precedence over shift_type_id.
       
       This handles edge cases where data might be inconsistent.
       
       Expected: Counter event type should be used
       """
   ```

4. **Maintain test data**
   - Keep mock data realistic
   - Update when schema changes
   - Document data structure

---

## Resources

### Documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Flask Testing](https://flask.palletsprojects.com/testing/)

### Project Files
- Backend tests: `backend/tests/`
- Frontend tests: `frontend/src/tests/`
- Test configuration: `backend/pytest.ini`, `frontend/vitest.config.js`
- Validation reports: `docs/agent/testing/`

---

**Last Updated:** November 10, 2025  
**Maintained By:** Development Team
