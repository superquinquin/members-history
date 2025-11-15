# Test Architecture - FTOP Shift Timeline Feature

## Test Pyramid

```
                    ▲
                   ╱ ╲
                  ╱   ╲
                 ╱  E2E ╲          (Manual Testing)
                ╱───────╲
               ╱         ╲
              ╱Integration╲        Backend: API Tests (7)
             ╱─────────────╲       Frontend: Component Tests (17)
            ╱               ╲
           ╱      Unit       ╲     Backend: Helper Function (10)
          ╱───────────────────╲    Frontend: Logic Functions (8)
         ╱                     ╲
        ╱_______________________╲
```

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ App.jsx                                              │   │
│  │                                                      │   │
│  │  getEventTitle()  ◄─── Unit Tests (8)              │   │
│  │  ├─ Check shift_type                                │   │
│  │  ├─ Return correct translation key                  │   │
│  │  └─ Handle edge cases                               │   │
│  │                                                      │   │
│  │  ShiftEvent Rendering  ◄─── Component Tests (17)   │   │
│  │  ├─ Warning badge (unknown type)                    │   │
│  │  ├─ FTOP indicator badge                            │   │
│  │  ├─ Counter badge (independent)                     │   │
│  │  └─ Visual consistency                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          │ HTTP Request                     │
│                          ▼                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      Backend (Flask)                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ app.py                                               │   │
│  │                                                      │   │
│  │  /api/member/<id>/history  ◄─── Integration (7)    │   │
│  │  ├─ Fetch shifts with shift_type_id                 │   │
│  │  ├─ Fetch counter events                            │   │
│  │  ├─ Call determine_shift_type()                     │   │
│  │  ├─ Build response with shift_type                  │   │
│  │  └─ Return JSON                                     │   │
│  │                                                      │   │
│  │  determine_shift_type()  ◄─── Unit Tests (10)      │   │
│  │  ├─ Check counter event type                        │   │
│  │  ├─ Check shift_type_id                             │   │
│  │  ├─ Handle 'volant' detection                       │   │
│  │  └─ Return 'ftop'/'standard'/'unknown'             │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          │ Odoo API Call                     │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ odoo_client.py                                       │   │
│  │                                                      │   │
│  │  get_member_shift_history()                         │   │
│  │  └─ Fetch with shift_type_id field                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       Odoo Database                          │
├─────────────────────────────────────────────────────────────┤
│  shift.registration                                          │
│  ├─ shift_id                                                 │
│  ├─ shift_type_id  ◄─── NEW FIELD                          │
│  └─ state (done/absent/excused)                             │
│                                                               │
│  shift.counter.event                                         │
│  ├─ shift_id                                                 │
│  ├─ type (ftop/standard)                                     │
│  └─ point_qty                                                │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────────┐
│ User Request │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ Frontend: GET /api/member/123/history                   │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Backend: app.py                                          │
│                                                          │
│ 1. Fetch shifts (with shift_type_id)                   │
│    ↓                                                     │
│ 2. Fetch counter events (with type field)              │
│    ↓                                                     │
│ 3. Build shift_counter_map                             │
│    ↓                                                     │
│ 4. For each shift:                                      │
│    ├─ shift_type = determine_shift_type(shift, map)    │
│    │   │                                                │
│    │   ├─ Check counter.type (priority 1)              │
│    │   ├─ Check shift_type_id (priority 2)             │
│    │   └─ Return 'ftop'/'standard'/'unknown'           │
│    │                                                     │
│    └─ Add shift_type to event                          │
│                                                          │
│ 5. Return events with shift_type field                 │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Frontend: App.jsx                                        │
│                                                          │
│ 1. Receive events                                       │
│    ↓                                                     │
│ 2. For each shift event:                               │
│    ├─ title = getEventTitle(event)                     │
│    │   │                                                │
│    │   ├─ Check event.shift_type                       │
│    │   ├─ Check event.state                            │
│    │   └─ Return translation key                       │
│    │                                                     │
│    ├─ Render title                                      │
│    ├─ Render FTOP indicator (if ftop)                  │
│    ├─ Render warning badge (if unknown)                │
│    └─ Render counter badge (if exists)                 │
│                                                          │
│ 3. Display in timeline                                  │
└─────────────────────────────────────────────────────────┘
```

## Test Coverage Map

```
Backend Tests (17 total)
├── Unit Tests (10) - test_determine_shift_type.py
│   ├── ✓ FTOP counter event
│   ├── ✓ Standard counter event
│   ├── ✓ No counter, FTOP shift_type_id
│   ├── ✓ No counter, Standard shift_type_id
│   ├── ✓ 'Volant' in name detection
│   ├── ✓ Missing shift_type_id
│   ├── ✓ Null shift_type_id
│   ├── ✓ Case-insensitive volant
│   ├── ✓ Counter precedence
│   └── ✓ shift_id format handling
│
└── Integration Tests (7) - test_member_history_api.py
    ├── ✓ FTOP member mixed shifts
    ├── ✓ Standard member only
    ├── ✓ Excused shift no counter
    ├── ✓ Missing shift_type_id
    ├── ✓ Counter data unchanged
    ├── ✓ Future shift
    └── ✓ Type mismatch

Frontend Tests (25 total)
├── Unit Tests (8) - getEventTitle.test.jsx
│   ├── ✓ FTOP attended
│   ├── ✓ FTOP missed
│   ├── ✓ FTOP excused
│   ├── ✓ Standard attended
│   ├── ✓ Standard missed
│   ├── ✓ Standard excused
│   ├── ✓ Unknown type
│   └── ✓ Missing shift_type
│
└── Component Tests (17) - ShiftDisplay.test.jsx
    ├── Warning Badge (3)
    │   ├── ✓ Shows for unknown
    │   ├── ✓ Hidden for FTOP
    │   └── ✓ Hidden for standard
    │
    ├── FTOP Indicator (3)
    │   ├── ✓ Shows for FTOP
    │   ├── ✓ Hidden for standard
    │   └── ✓ Hidden for unknown
    │
    ├── Counter Badge (5)
    │   ├── ✓ FTOP counter displays
    │   ├── ✓ Standard counter displays
    │   ├── ✓ Hidden when no counter
    │   ├── ✓ Negative values formatted
    │   └── ✓ Independent of shift_type
    │
    └── Mixed Scenarios (6)
        ├── ✓ FTOP + FTOP counter
        ├── ✓ Unknown + no counter
        └── ✓ Various combinations
```

## Decision Tree (determine_shift_type)

```
                    ┌─────────────────┐
                    │ Shift Event     │
                    └────────┬────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │ Has counter event?     │
                └────┬──────────────┬────┘
                     │ YES          │ NO
                     ▼              ▼
           ┌──────────────┐   ┌────────────────┐
           │ counter.type │   │ Has            │
           │ = 'ftop'?    │   │ shift_type_id? │
           └──┬────────┬──┘   └───┬────────┬───┘
              │ YES    │ NO       │ YES    │ NO
              ▼        ▼          ▼        ▼
           ┌────┐  ┌─────────┐ ┌──────────────┐ ┌─────────┐
           │ftop│  │standard │ │ 'ftop' or    │ │unknown  │
           └────┘  └─────────┘ │ 'volant' in  │ └─────────┘
                                │ name?        │
                                └──┬────────┬──┘
                                   │ YES    │ NO
                                   ▼        ▼
                                ┌────┐  ┌─────────┐
                                │ftop│  │standard │
                                └────┘  └─────────┘
```

## Test Execution Flow

```
1. Install Dependencies
   ├─ Backend: pip install -r requirements-dev.txt
   └─ Frontend: npm install

2. Run Tests (TDD - expect failures)
   ├─ Backend: pytest -v
   └─ Frontend: npm test

3. Implement Feature
   ├─ Backend: Add determine_shift_type()
   ├─ Backend: Update API endpoint
   ├─ Frontend: Update getEventTitle()
   └─ Frontend: Add visual indicators

4. Verify Tests Pass
   ├─ Backend: pytest --cov
   └─ Frontend: npm run test:coverage

5. Manual Testing
   └─ Test in browser with real data

6. Coverage Verification
   ├─ Backend: ≥ 85%
   └─ Frontend: ≥ 80%
```

## Critical Paths Tested

```
Happy Path:
User → Search Member → View History → See FTOP Shifts → Correct Labels

Edge Cases:
├─ Excused Shift (no counter) → Uses shift_type_id
├─ Future Shift (not closed) → Uses shift_type_id
├─ Legacy Data (no shift_type_id) → Shows 'unknown' warning
├─ Type Mismatch → Counter type takes precedence
└─ Mixed Timeline → Both types display correctly
```

## Test Dependencies

```
Backend:
pytest ──────► test_determine_shift_type.py
pytest-mock ─► test_member_history_api.py
pytest-flask ► test_member_history_api.py
pytest-cov ──► Coverage reporting

Frontend:
vitest ──────────────► All tests
@testing-library/react ► Component tests
happy-dom ───────────► DOM simulation
```

## Success Metrics

```
Code Coverage:
├─ determine_shift_type(): 100% ✓
├─ API endpoint: 90%+ ✓
├─ getEventTitle(): 100% ✓
└─ Shift rendering: 95%+ ✓

Test Count:
├─ Backend: 17 tests ✓
├─ Frontend: 25 tests ✓
└─ Total: 42 tests ✓

Quality:
├─ All tests pass ✓
├─ No regressions ✓
└─ Edge cases covered ✓
```
