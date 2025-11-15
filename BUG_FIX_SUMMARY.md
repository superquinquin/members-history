# Bug Fix Summary: FTOP Shift Timeline Display

## Date
November 11, 2025

## Issues Fixed

### Issue 1: Wrong Labels on Standard Shifts for FTOP Members
**Problem:** FTOP member "PONS, Ariane" had standard ABCD shifts (shift_type_id=[1, 'ABCD Shift']) incorrectly labeled as "FTOP Shift attended"

**Root Cause:** The `determine_shift_type()` function prioritized counter event type over shift_type_id. For FTOP members, ALL counter events have `type='ftop'` (even for standard ABCD shifts they attend), causing standard shifts to be mislabeled.

**Fix:** Reversed the priority in `determine_shift_type()`:
- **Primary source:** shift_type_id (what kind of shift it actually is)
- **Fallback source:** counter event type (only if shift_type_id missing)

**File:** `backend/app.py` (lines 84-121)

### Issue 2: Missing FTOP Shifts with 'open' State
**Problem:** FTOP shift "Service volants - BSam. - 21:00" (04/10/2025) didn't appear in timeline

**Root Cause:** The shift registration had `state='open'`, but `get_member_shift_history()` only fetched shifts with `state in ['done', 'absent', 'excused']`

**Fix:** Added 'open' state to the shift history query to include registered but not yet completed shifts.

**File:** `backend/odoo_client.py` (line 118)

## Files Modified

### 1. `backend/app.py`
- Updated `determine_shift_type()` function to prioritize shift_type_id over counter event type
- Added warning message when using counter type as fallback

### 2. `backend/odoo_client.py`
- Added 'open' state to shift history query domain

### 3. `backend/tests/test_determine_shift_type.py`
- Updated test `test_counter_event_takes_precedence_over_shift_type_id` → `test_shift_type_id_takes_precedence_over_counter_event`
- Updated test expectations to reflect new priority order

### 4. `backend/tests/test_member_history_api.py`
- Updated test `test_type_mismatch_counter_vs_shift_type_id` to expect 'standard' instead of 'ftop'
- Updated test documentation to explain real-world FTOP member behavior

## Test Results

### Unit Tests
✅ All 17 tests passing:
- 10 tests in `test_determine_shift_type.py`
- 7 tests in `test_member_history_api.py`

### Manual Testing with Real Data
Tested with member 5268 (Ariane PONS):
- ✅ ABCD shifts correctly labeled as 'standard' (shift_type='standard')
- ✅ FTOP shifts correctly labeled as 'ftop' (shift_type='ftop')
- ✅ Open state shifts now included in timeline (5 open shifts found)
- ✅ API returns correct shift_type for all 50 shifts

## Impact

### Before Fix
- FTOP members' standard ABCD shifts were mislabeled as "FTOP Shift attended"
- FTOP shifts with state='open' were missing from timeline
- Confusing user experience for FTOP members viewing their history

### After Fix
- All shifts correctly labeled based on their actual type (shift_type_id)
- All registered shifts visible in timeline, including future/open shifts
- Clear distinction between standard ABCD shifts and FTOP shifts
- Accurate timeline representation for FTOP members

## Backward Compatibility

✅ Fully backward compatible:
- Fallback logic preserved for shifts without shift_type_id
- Counter event aggregation unchanged
- API response structure unchanged
- Existing tests updated to reflect correct behavior

## Verification

To verify the fixes work:

```bash
# Run all backend tests
cd backend && python -m pytest tests/ -v

# Test with a specific FTOP member
cd backend && python -c "
from odoo_client import OdooClient
odoo = OdooClient()
odoo.authenticate()
shifts = odoo.get_member_shift_history(5268, limit=10)
for shift in shifts[:5]:
    print(f'{shift[\"date_begin\"]} - {shift[\"shift_name\"]}')
    print(f'  shift_type_id: {shift[\"shift_type_id\"]}')
    print(f'  state: {shift[\"state\"]}')
"
```

## Related Documentation

- User testing feedback: `docs/agent/testing/2025-11-10-ftop-shift-timeline-validation.md`
- Test architecture: `TEST_ARCHITECTURE.md`
- Testing guide: `docs/agent/testing/testing-guide.md`
