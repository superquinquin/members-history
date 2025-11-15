# FTOP Shift Timeline Feature - Implementation Checklist

## Overview

This checklist guides you through implementing the FTOP shift timeline feature using the comprehensive test suite that has been created.

## Prerequisites

✅ Tests have been written (TDD approach)  
✅ Test infrastructure is set up  
✅ Requirements are documented  

## Step 1: Set Up Test Environment

### Backend
```bash
cd backend
pip install -r requirements-dev.txt
pytest -v  # Should show failures - this is expected!
```

**Expected**: All tests fail because functions don't exist yet.

### Frontend
```bash
cd frontend
npm install  # Installs test dependencies
npm test     # Should show failures - this is expected!
```

**Expected**: All tests fail because implementation is missing.

## Step 2: Backend Implementation

### 2.1 Update `odoo_client.py`

**File**: `backend/odoo_client.py`

**Change**: Add `'shift_type_id'` to shift_fields array

**Location**: Line ~120 in `get_member_shift_history()` method

```python
# BEFORE:
fields = ['id', 'date_begin', 'date_end', 'state', 'shift_id', 'is_late']

# AFTER:
fields = ['id', 'date_begin', 'date_end', 'state', 'shift_id', 'is_late', 'shift_type_id']
```

**Test**: Run `pytest tests/test_member_history_api.py -v`

### 2.2 Create `determine_shift_type()` helper in `app.py`

**File**: `backend/app.py`

**Location**: Add after imports, before routes (around line 12)

```python
def determine_shift_type(shift: Dict, shift_counter_map: Dict) -> str:
    """
    Determine the shift type (ftop, standard, or unknown).
    
    Priority:
    1. Counter event type (if exists)
    2. shift_type_id field
    3. 'unknown' if neither available
    
    Args:
        shift: Shift registration dict from Odoo
        shift_counter_map: Map of shift_id to counter data
    
    Returns:
        'ftop', 'standard', or 'unknown'
    """
    # Extract shift_id (handle both list and int formats)
    shift_id = shift.get('shift_id')
    if isinstance(shift_id, list):
        shift_id = shift_id[0]
    
    # Priority 1: Check counter event type
    if shift_id and shift_id in shift_counter_map:
        counter_type = shift_counter_map[shift_id].get('type', '')
        if counter_type in ['ftop', 'standard']:
            return counter_type
    
    # Priority 2: Check shift_type_id field
    shift_type_id = shift.get('shift_type_id')
    if shift_type_id and shift_type_id is not False:
        if isinstance(shift_type_id, list) and len(shift_type_id) >= 2:
            type_name = shift_type_id[1].lower() if shift_type_id[1] else ''
            
            # Check for FTOP indicators
            if 'ftop' in type_name or 'volant' in type_name:
                return 'ftop'
            elif 'standard' in type_name:
                return 'standard'
    
    # Default: unknown
    return 'unknown'
```

**Test**: Run `pytest tests/test_determine_shift_type.py -v`

**Expected**: All unit tests should pass.

### 2.3 Update `/api/member/<id>/history` endpoint

**File**: `backend/app.py`

**Location**: In `get_member_history()` function, around line 246-266

**Change**: Add shift_type and shift_type_id to shift events

```python
# FIND this section (around line 246):
if shifts:
    for shift in shifts:
        shift_id = shift.get('shift_id')
        if isinstance(shift_id, list):
            shift_id = shift_id[0]
        
        shift_event = {
            'type': 'shift',
            'id': shift.get('id'),
            'date': shift.get('date_begin'),
            'shift_name': shift.get('shift_name'),
            'state': shift.get('state'),
            'is_late': shift.get('is_late', False),
            'week_number': shift.get('week_number'),
            'week_name': shift.get('week_name')
        }

# ADD these two lines:
        shift_event['shift_type'] = determine_shift_type(shift, shift_counter_map)
        shift_event['shift_type_id'] = shift.get('shift_type_id')  # For debugging
        
        # ... rest of the code continues unchanged
```

**Test**: Run `pytest tests/test_member_history_api.py -v`

**Expected**: All integration tests should pass.

### 2.4 Verify Backend Tests

```bash
cd backend
pytest -v --cov=app --cov=odoo_client --cov-report=html
```

**Expected**:
- ✅ All tests pass
- ✅ Coverage ≥ 85%
- ✅ `determine_shift_type()` coverage = 100%

## Step 3: Frontend Implementation

### 3.1 Update Translations

**Files**: 
- `frontend/src/locales/en.json`
- `frontend/src/locales/fr.json`

**Change**: Add FTOP-specific translations

**en.json** - Add to "timeline" section:
```json
{
  "timeline": {
    ...existing translations...,
    "ftopShiftAttended": "FTOP Shift Attended",
    "ftopShiftMissed": "FTOP Shift Missed",
    "ftopShiftExcused": "FTOP Shift Excused",
    "unknownShiftType": "Unknown Shift Type"
  }
}
```

**fr.json** - Add to "timeline" section:
```json
{
  "timeline": {
    ...existing translations...,
    "ftopShiftAttended": "Présence au Créneau Vacation",
    "ftopShiftMissed": "Absence au Créneau Vacation",
    "ftopShiftExcused": "Absence Excusée Vacation",
    "unknownShiftType": "Type de Créneau Inconnu"
  }
}
```

**Test**: Run `npm test -- src/tests/getEventTitle.test.jsx`

### 3.2 Update `getEventTitle()` in `App.jsx`

**File**: `frontend/src/App.jsx`

**Location**: Around line 474-483 (inside the event rendering section)

**Change**: Update shift title logic to check `shift_type`

```javascript
// FIND:
const getEventTitle = () => {
  if (event.type === 'purchase') return t('timeline.purchase')
  if (event.type === 'leave_start') return t('timeline.leaveStart')
  if (event.type === 'leave_end') return t('timeline.leaveEnd')
  if (event.type === 'counter') return t('counter.manual')
  if (event.type === 'shift' && event.state === 'done') return t('timeline.shiftAttended')
  if (event.type === 'shift' && event.state === 'absent') return t('timeline.shiftMissed')
  if (event.type === 'shift' && event.state === 'excused') return t('timeline.shiftExcused')
  return event.type
}

// REPLACE WITH:
const getEventTitle = () => {
  if (event.type === 'purchase') return t('timeline.purchase')
  if (event.type === 'leave_start') return t('timeline.leaveStart')
  if (event.type === 'leave_end') return t('timeline.leaveEnd')
  if (event.type === 'counter') return t('counter.manual')
  
  if (event.type === 'shift') {
    // FTOP shift titles
    if (event.shift_type === 'ftop') {
      if (event.state === 'done') return t('timeline.ftopShiftAttended')
      if (event.state === 'absent') return t('timeline.ftopShiftMissed')
      if (event.state === 'excused') return t('timeline.ftopShiftExcused')
    }
    
    // Standard shift titles (default)
    if (event.state === 'done') return t('timeline.shiftAttended')
    if (event.state === 'absent') return t('timeline.shiftMissed')
    if (event.state === 'excused') return t('timeline.shiftExcused')
  }
  
  return event.type
}
```

**Test**: Run `npm test -- src/tests/getEventTitle.test.jsx`

**Expected**: All getEventTitle tests should pass.

### 3.3 Add Visual Indicators (Optional Enhancement)

**File**: `frontend/src/App.jsx`

**Location**: Inside the event rendering, around line 494 (after the title)

**Add**: Warning badge for unknown shift types

```jsx
<div className="flex items-center gap-2">
  <span className="font-semibold text-gray-900">{getEventTitle()}</span>
  
  {/* Warning badge for unknown shift type */}
  {event.type === 'shift' && event.shift_type === 'unknown' && (
    <span className="text-xs bg-orange-200 text-orange-800 px-2 py-0.5 rounded-full">
      ⚠️ {t('timeline.unknownShiftType')}
    </span>
  )}
  
  {/* FTOP indicator badge */}
  {event.type === 'shift' && event.shift_type === 'ftop' && (
    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
      ⏱️ {t('counter.ftop_short')}
    </span>
  )}
  
  {event.duringLeave && (
    <span className="text-xs bg-yellow-200 text-yellow-800 px-2 py-0.5 rounded-full">
      {t('timeline.duringLeave')}
    </span>
  )}
</div>
```

**Test**: Run `npm test -- src/tests/ShiftDisplay.test.jsx`

**Expected**: All component tests should pass.

### 3.4 Verify Frontend Tests

```bash
cd frontend
npm test -- --coverage
```

**Expected**:
- ✅ All tests pass
- ✅ Coverage ≥ 80%
- ✅ getEventTitle() coverage = 100%

## Step 4: Integration Testing

### 4.1 Start Backend

```bash
cd backend
python app.py
```

### 4.2 Start Frontend

```bash
cd frontend
npm run dev
```

### 4.3 Manual Testing Checklist

- [ ] Search for a FTOP member
- [ ] Verify FTOP shifts show "FTOP Shift Attended/Missed/Excused"
- [ ] Verify standard shifts show "Shift Attended/Missed/Excused"
- [ ] Check that FTOP indicator badge appears (⏱️)
- [ ] Check counter badges still work correctly
- [ ] Test with a member who has both shift types
- [ ] Verify excused shifts display correctly
- [ ] Check that unknown shifts show warning badge

## Step 5: Final Verification

### Run All Tests

```bash
# Backend
cd backend
pytest -v --cov=app --cov=odoo_client --cov-report=html

# Frontend
cd frontend
npm test -- --coverage
```

### Success Criteria

- ✅ All backend tests pass (17+ tests)
- ✅ All frontend tests pass (25+ tests)
- ✅ Backend coverage ≥ 85%
- ✅ Frontend coverage ≥ 80%
- ✅ Manual testing checklist complete
- ✅ No console errors in browser
- ✅ No Python errors in backend

## Step 6: Documentation

- [ ] Update `specs/features.md` if needed
- [ ] Add any edge cases discovered to test suite
- [ ] Update CHANGELOG (if exists)
- [ ] Mark this feature as complete

## Troubleshooting

### Backend Tests Failing

```bash
# Run with verbose output
pytest -v -s

# Run specific test
pytest tests/test_determine_shift_type.py::TestDetermineShiftType::test_shift_with_ftop_counter_event -v

# Check imports
python -c "from app import determine_shift_type; print('OK')"
```

### Frontend Tests Failing

```bash
# Run with UI for debugging
npm run test:ui

# Run specific test
npm test -- src/tests/getEventTitle.test.jsx

# Check for syntax errors
npm run lint
```

### Visual Issues

1. Check browser console for errors
2. Verify API response includes `shift_type` field
3. Check translation keys are correct
4. Inspect element to verify CSS classes

## Rollback Plan

If issues arise:

1. Backend: Remove `shift_type` and `shift_type_id` from shift events
2. Frontend: Revert `getEventTitle()` to original version
3. Remove visual indicators
4. Tests will fail but app will work with original functionality

## Notes

- All error imports in tests are **expected** until implementation is complete
- Tests are designed to **fail first** (TDD approach)
- Each test should pass **incrementally** as you implement
- Keep tests **green** - don't break existing functionality

## Success! 🎉

When all steps are complete:
- ✅ Feature fully implemented
- ✅ All tests passing
- ✅ Coverage goals met
- ✅ Documentation updated
- ✅ Ready for production
