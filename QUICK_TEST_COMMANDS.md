# Quick Test Commands Reference

## Backend Tests

### Run All Tests
```bash
cd backend
pytest -v
```

### Run with Coverage
```bash
cd backend
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Run Specific Test
```bash
cd backend
pytest tests/test_determine_shift_type.py::TestDetermineShiftType::test_shift_with_ftop_counter_event -v
```

### Run Tests Matching Pattern
```bash
cd backend
pytest -k "ftop" -v
```

### Run Only Unit Tests
```bash
cd backend
pytest tests/test_determine_shift_type.py -v
```

### Run Only Integration Tests
```bash
cd backend
pytest tests/test_member_history_api.py -v
```

## Frontend Tests

### Run All Tests (Exit After)
```bash
cd frontend
npm test -- --run
```

### Run in Watch Mode
```bash
cd frontend
npm test
```

### Run Specific Test File
```bash
cd frontend
npm test -- src/tests/getEventTitle.test.jsx --run
```

### Run Tests Matching Pattern
```bash
cd frontend
npm test -- --grep "FTOP" --run
```

### Run with Coverage
```bash
cd frontend
npm run test:coverage
```

## Both Backend and Frontend

### Run All Tests
```bash
# Terminal 1
cd backend && pytest -v

# Terminal 2
cd frontend && npm test -- --run
```

### Run with Coverage
```bash
# Terminal 1
cd backend && pytest --cov=. --cov-report=html

# Terminal 2
cd frontend && npm run test:coverage
```

## Development Workflow

### Watch Mode (for development)
```bash
# Terminal 1 - Backend
cd backend
pytest -v --tb=short

# Terminal 2 - Frontend
cd frontend
npm test
```

### Before Committing
```bash
# Backend
cd backend
pytest -v
pytest --cov=. --cov-report=term-missing

# Frontend
cd frontend
npm test -- --run
npm run lint
```

## Troubleshooting

### Backend: Module not found
```bash
cd backend
pip install -r requirements-dev.txt
```

### Frontend: Dependency issues
```bash
cd frontend
npm install --legacy-peer-deps
```

### Clear cache and reinstall
```bash
# Backend
cd backend
rm -rf .pytest_cache
pip install -r requirements-dev.txt

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

## Test Results

- **Backend:** 17 tests, 100% pass rate
- **Frontend:** 22 tests, 100% pass rate
- **Total:** 39 tests, 100% pass rate

See `TEST_RESULTS.md` for detailed results.
See `docs/agent/testing/2025-11-10-ftop-shift-timeline-validation.md` for full validation report.
