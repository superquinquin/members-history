# Quick Test Reference - FTOP Shift Timeline

## One-Liner Commands

### Backend
```bash
# Run all tests
cd backend && pytest

# Run with coverage
cd backend && pytest --cov --cov-report=html && open htmlcov/index.html

# Run specific test
cd backend && pytest tests/test_determine_shift_type.py -v

# Watch mode (requires pytest-watch)
cd backend && ptw
```

### Frontend
```bash
# Run all tests
cd frontend && npm test

# Run with coverage
cd frontend && npm run test:coverage

# Run with UI
cd frontend && npm run test:ui

# Watch mode
cd frontend && npm test -- --watch
```

## Test File Locations

```
backend/tests/
├── test_determine_shift_type.py    # Unit tests (10 tests)
└── test_member_history_api.py      # Integration tests (7 tests)

frontend/src/tests/
├── getEventTitle.test.jsx          # Unit tests (8 tests)
└── ShiftDisplay.test.jsx           # Component tests (17 tests)
```

## Quick Test Status Check

```bash
# Backend
cd backend && pytest --tb=no -q

# Frontend
cd frontend && npm test -- --reporter=verbose

# Both (from project root)
(cd backend && pytest --tb=no -q) && (cd frontend && npm test -- --run)
```

## Coverage Goals

| Component | Goal | Command |
|-----------|------|---------|
| Backend | 85%+ | `cd backend && pytest --cov` |
| Frontend | 80%+ | `cd frontend && npm run test:coverage` |

## Test Count Summary

- **Backend**: 17 tests (10 unit + 7 integration)
- **Frontend**: 25 tests (8 unit + 17 component)
- **Total**: 42 tests

## Installation

```bash
# Backend
cd backend && pip install -r requirements-dev.txt

# Frontend
cd frontend && npm install
```

## Expected Behavior (Before Implementation)

❌ All tests should **FAIL** - this is correct!  
✅ Tests define the expected behavior  
⏳ Implementation will make them pass  

## Expected Behavior (After Implementation)

✅ All tests should **PASS**  
✅ Coverage should meet goals  
✅ No regressions in existing features  

## Debugging

```bash
# Backend - verbose with stdout
cd backend && pytest -v -s

# Backend - stop at first failure
cd backend && pytest -x

# Frontend - UI debugger
cd frontend && npm run test:ui
```

## Documentation

- **TESTING.md** - Comprehensive guide
- **TEST_SUMMARY.md** - Executive summary
- **IMPLEMENTATION_CHECKLIST.md** - Step-by-step implementation
- **This file** - Quick reference

## Support

All import errors are **expected** until implementation is complete.
The errors indicate missing functions that tests are designed to verify.
