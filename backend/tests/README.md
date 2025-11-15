# Backend Tests for FTOP Shift Timeline

## Quick Start

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov=odoo_client --cov-report=html
```

## Test Files

- **`conftest.py`** - Shared fixtures and test configuration
- **`mock_data.py`** - Sample data for different scenarios
- **`test_determine_shift_type.py`** - Unit tests for shift type determination logic
- **`test_member_history_api.py`** - Integration tests for API endpoint

## Test Scenarios Covered

### Unit Tests (determine_shift_type)
- ✅ Shift with FTOP counter event
- ✅ Shift with standard counter event
- ✅ Excused shift without counter (uses shift_type_id)
- ✅ Shift with 'volant' in name (case-insensitive)
- ✅ Legacy shift without shift_type_id (returns 'unknown')
- ✅ Counter type precedence over shift_type_id
- ✅ Both list and integer shift_id formats

### Integration Tests (API)
- ✅ FTOP member with mixed shift types
- ✅ Standard member with only standard shifts
- ✅ Excused shifts without counter events
- ✅ Shifts with missing shift_type_id
- ✅ Counter data integrity
- ✅ Future shifts not yet closed
- ✅ Type mismatch scenarios

## Running Specific Tests

```bash
# Run one test file
pytest tests/test_determine_shift_type.py

# Run one test class
pytest tests/test_determine_shift_type.py::TestDetermineShiftType

# Run one specific test
pytest tests/test_determine_shift_type.py::TestDetermineShiftType::test_shift_with_ftop_counter_event

# Run with verbose output
pytest -v

# Stop at first failure
pytest -x
```

## Coverage Goals

- **Overall**: 85%+
- **determine_shift_type()**: 100%
- **API endpoint**: 90%+

## Note

These tests are written **BEFORE** implementation (TDD approach).
They will fail until the feature is implemented.
