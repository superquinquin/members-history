# Testing Guide for FTOP Shift Timeline Feature

## Overview

This document provides comprehensive testing documentation for the FTOP shift timeline display feature. The feature enables the application to correctly identify and display FTOP (Service Volants) shifts separately from standard ABCD shifts.

## Test Infrastructure Setup

### Backend Tests (Python/pytest)

#### Installation

```bash
cd backend

# Install development dependencies
pip install -r requirements-dev.txt

# Or manually:
pip install pytest pytest-cov pytest-mock pytest-flask
```

#### Configuration

The backend uses **pytest** as the testing framework with the following plugins:
- `pytest-cov`: Code coverage reporting
- `pytest-mock`: Mocking support
- `pytest-flask`: Flask application testing utilities

#### Running Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_determine_shift_type.py

# Run specific test class or function
pytest tests/test_determine_shift_type.py::TestDetermineShiftType::test_shift_with_ftop_counter_event

# Run with coverage report
pytest --cov=app --cov=odoo_client --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Frontend Tests (JavaScript/Vitest)

#### Installation

```bash
cd frontend

# Install dependencies (includes test dependencies)
npm install
```

#### Configuration

The frontend uses **Vitest** with React Testing Library:
- `vitest`: Fast unit test framework (Vite-native)
- `@testing-library/react`: React component testing
- `@testing-library/jest-dom`: Custom matchers
- `happy-dom`: Lightweight DOM environment

Configuration is in `vitest.config.js`.

#### Running Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode (auto-rerun on changes)
npm test -- --watch

# Run with UI (visual test runner)
npm run test:ui

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- src/tests/getEventTitle.test.jsx
```

## Test Structure

### Backend Tests

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Shared fixtures and configuration
│   ├── mock_data.py                     # Sample data for testing
│   ├── test_determine_shift_type.py     # Unit tests for shift type logic
│   └── test_member_history_api.py       # Integration tests for API endpoint
├── requirements-dev.txt                 # Development dependencies
└── app.py                               # Application code
```

### Frontend Tests

```
frontend/
├── src/
│   └── tests/
│       ├── setup.js                     # Test environment setup
│       ├── getEventTitle.test.jsx       # Unit tests for title logic
│       └── ShiftDisplay.test.jsx        # Component rendering tests
├── vitest.config.js                     # Vitest configuration
└── package.json                         # Dependencies
```

## Test Coverage

### Backend Test Coverage

#### Unit Tests (`test_determine_shift_type.py`)

**Target: `determine_shift_type()` helper function**

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_shift_with_ftop_counter_event` | Shift has counter with `type='ftop'` | Returns `'ftop'` |
| `test_shift_with_standard_counter_event` | Shift has counter with `type='standard'` | Returns `'standard'` |
| `test_shift_without_counter_with_ftop_shift_type_id` | No counter, but `shift_type_id=[1, 'FTOP']` | Returns `'ftop'` |
| `test_shift_without_counter_with_standard_shift_type_id` | No counter, but `shift_type_id=[2, 'Standard']` | Returns `'standard'` |
| `test_shift_with_volant_in_shift_type_name` | `shift_type_id` contains 'volant' | Returns `'ftop'` |
| `test_shift_without_counter_and_without_shift_type_id` | No counter, no `shift_type_id` | Returns `'unknown'` |
| `test_shift_with_null_shift_type_id` | `shift_type_id=False` (Odoo null) | Returns `'unknown'` |
| `test_shift_type_case_insensitive_volant` | 'Volant', 'VOLANT', etc. | All return `'ftop'` |
| `test_counter_event_takes_precedence_over_shift_type_id` | Counter type conflicts with shift_type_id | Counter type wins |
| `test_shift_id_as_integer` | Handles both `[id, name]` and `id` formats | Both work correctly |

**Coverage Goal: 100% of `determine_shift_type()` function**

#### Integration Tests (`test_member_history_api.py`)

**Target: `/api/member/<id>/history` endpoint**

| Test Case | Description | Validates |
|-----------|-------------|-----------|
| `test_ftop_member_with_mixed_shift_types` | FTOP member with both shift types | Response includes correct `shift_type` for each |
| `test_standard_member_with_only_standard_shifts` | Standard ABCD member | All shifts have `shift_type='standard'` |
| `test_excused_shift_without_counter_event` | Excused shift (no counter) | Type determined from `shift_type_id` |
| `test_shift_with_missing_shift_type_id` | Legacy data without type | Returns `shift_type='unknown'` |
| `test_counter_data_unchanged` | Existing counter functionality | Counter data remains correct |
| `test_future_shift_not_yet_closed` | Future shift without counter | Type determined from `shift_type_id` |
| `test_type_mismatch_counter_vs_shift_type_id` | Data inconsistency | Counter type takes precedence |

**Coverage Goal: 90%+ of `/api/member/<id>/history` endpoint**

### Frontend Test Coverage

#### Unit Tests (`getEventTitle.test.jsx`)

**Target: `getEventTitle()` function**

| Test Case | Description | Expected Translation Key |
|-----------|-------------|-------------------------|
| FTOP shift attended | `shift_type='ftop'`, `state='done'` | `'timeline.ftopShiftAttended'` |
| FTOP shift missed | `shift_type='ftop'`, `state='absent'` | `'timeline.ftopShiftMissed'` |
| FTOP shift excused | `shift_type='ftop'`, `state='excused'` | `'timeline.ftopShiftExcused'` |
| Standard shift attended | `shift_type='standard'`, `state='done'` | `'timeline.shiftAttended'` |
| Standard shift missed | `shift_type='standard'`, `state='absent'` | `'timeline.shiftMissed'` |
| Standard shift excused | `shift_type='standard'`, `state='excused'` | `'timeline.shiftExcused'` |
| Unknown shift type | `shift_type='unknown'` | Default shift title |
| Missing shift type | No `shift_type` field | Default shift title |

**Coverage Goal: 100% of `getEventTitle()` logic**

#### Component Tests (`ShiftDisplay.test.jsx`)

**Target: Shift event rendering in timeline**

| Test Case | Description | Visual Result |
|-----------|-------------|---------------|
| Unknown type warning | `shift_type='unknown'` | ⚠️ warning badge appears |
| FTOP indicator display | `shift_type='ftop'` | ⏱️ FTOP badge appears |
| Standard shift (no indicator) | `shift_type='standard'` | No special badge |
| Counter badge independence | Any shift with counter | Counter badge displays regardless of type |
| FTOP shift with FTOP counter | Both FTOP type and counter | Both indicators show |
| Negative counter values | `point_qty < 0` | Displays `-1` not `+-1` |

**Coverage Goal: 95%+ of shift event rendering logic**

## Critical Test Scenarios

### Edge Cases to Cover

1. **Excused Shifts (No Counter)**
   - Excused shifts don't generate counter events
   - Must rely on `shift_type_id` field
   - Test: `test_excused_shift_without_counter_event`

2. **Future Shifts**
   - Shifts scheduled but not yet closed
   - No counter event generated yet
   - Test: `test_future_shift_not_yet_closed`

3. **Missing `shift_type_id`**
   - Legacy data before field was added
   - Should return `'unknown'` and show warning
   - Test: `test_shift_without_counter_and_without_shift_type_id`

4. **Type Mismatch**
   - Counter type differs from `shift_type_id`
   - Counter should take precedence (source of truth)
   - Test: `test_type_mismatch_counter_vs_shift_type_id`

5. **Mixed Shift Types in Timeline**
   - FTOP members can have both FTOP and standard shifts
   - Each must be correctly identified
   - Test: `test_ftop_member_with_mixed_shift_types`

6. **Case-Insensitive 'Volant' Detection**
   - 'Service Volant', 'VOLANT', 'volant' all mean FTOP
   - Test: `test_shift_type_case_insensitive_volant`

## Mock Data

Sample data is provided in `backend/tests/mock_data.py`:

- `FTOP_MEMBER_MIXED_SHIFTS`: FTOP member with both shift types
- `STANDARD_MEMBER`: Standard ABCD member only
- `EXCUSED_SHIFT_NO_COUNTER`: Excused shift without counter
- `LEGACY_SHIFT_NO_TYPE_ID`: Old data without `shift_type_id`
- `SERVICE_VOLANT_SHIFT`: Shift with 'Service Volant' name
- `TYPE_MISMATCH`: Inconsistent counter and shift_type_id
- `EXPECTED_FTOP_MEMBER_RESPONSE`: Expected API response structure

## Continuous Integration

### Pre-commit Checks

```bash
# Run before committing
cd backend && pytest
cd frontend && npm test
```

### Coverage Thresholds

**Backend:**
- Overall: 85%+
- `determine_shift_type()`: 100%
- `/api/member/<id>/history`: 90%+

**Frontend:**
- Overall: 80%+
- `getEventTitle()`: 100%
- Shift rendering components: 95%+

### CI/CD Integration

Add to your CI pipeline (GitHub Actions, GitLab CI, etc.):

```yaml
# Example GitHub Actions workflow
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt
          pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: |
          cd frontend
          npm ci
          npm test -- --coverage
      - uses: codecov/codecov-action@v3
```

## Test-Driven Development Workflow

This test suite was created **BEFORE** implementation (TDD approach):

1. ✅ **Write tests first** - Define expected behavior
2. ❌ **Run tests** - They should fail (no implementation yet)
3. ✅ **Implement feature** - Make tests pass
4. ✅ **Refactor** - Improve code while keeping tests green
5. ✅ **Verify coverage** - Ensure all paths tested

## Debugging Failed Tests

### Backend

```bash
# Run with verbose output and print statements
pytest -v -s

# Run specific failing test
pytest tests/test_determine_shift_type.py::TestDetermineShiftType::test_shift_with_ftop_counter_event -v

# Use pdb debugger
pytest --pdb

# Stop at first failure
pytest -x
```

### Frontend

```bash
# Run with UI for visual debugging
npm run test:ui

# Run specific test file
npm test -- src/tests/getEventTitle.test.jsx

# Watch mode for iterative debugging
npm test -- --watch
```

## Maintenance

### Updating Tests

When modifying the FTOP shift feature:

1. Update tests FIRST to reflect new requirements
2. Run tests to verify they fail as expected
3. Implement changes
4. Verify all tests pass
5. Update this documentation

### Adding New Test Cases

Follow existing patterns:

**Backend:**
```python
def test_new_scenario(self, sample_fixture):
    """Test description."""
    from app import determine_shift_type
    
    # Arrange
    shift = {...}
    shift_counter_map = {...}
    
    # Act
    result = determine_shift_type(shift, shift_counter_map)
    
    # Assert
    assert result == 'expected_value', "Failure message"
```

**Frontend:**
```javascript
it('test description', () => {
  // Arrange
  const event = { ... }
  
  // Act
  const result = getEventTitle(event, mockT)
  
  // Assert
  expect(result).toBe('Expected Value')
})
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Vitest documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://testingjavascript.com/)

## Contact

For questions about the test suite, consult:
- Project documentation in `/docs`
- Code comments in test files
- This testing guide
