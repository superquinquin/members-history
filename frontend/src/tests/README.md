# Frontend Tests for FTOP Shift Timeline

## Quick Start

```bash
# Install dependencies (from frontend/ directory)
npm install

# Run tests
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

## Test Files

- **`setup.js`** - Test environment configuration and i18n mocking
- **`getEventTitle.test.jsx`** - Unit tests for event title logic
- **`ShiftDisplay.test.jsx`** - Component tests for shift rendering

## Test Scenarios Covered

### Unit Tests (getEventTitle)
- ✅ FTOP shift attended → 'timeline.ftopShiftAttended'
- ✅ FTOP shift missed → 'timeline.ftopShiftMissed'
- ✅ FTOP shift excused → 'timeline.ftopShiftExcused'
- ✅ Standard shift attended → 'timeline.shiftAttended'
- ✅ Standard shift missed → 'timeline.shiftMissed'
- ✅ Standard shift excused → 'timeline.shiftExcused'
- ✅ Unknown shift type → default title
- ✅ Missing shift_type field → default title

### Component Tests (ShiftDisplay)
- ✅ Warning badge for unknown shift type
- ✅ FTOP indicator badge for FTOP shifts
- ✅ No indicator for standard shifts
- ✅ Counter badge displays independently
- ✅ Both FTOP indicator and counter can show together
- ✅ Negative counter values formatted correctly

## Running Specific Tests

```bash
# Run one test file
npm test -- src/tests/getEventTitle.test.jsx

# Run in watch mode
npm test -- --watch

# Run with UI (recommended for debugging)
npm run test:ui
```

## Coverage Goals

- **Overall**: 80%+
- **getEventTitle()**: 100%
- **Shift rendering**: 95%+

## Note

These tests are written **BEFORE** implementation (TDD approach).
They define the expected behavior of the feature.
