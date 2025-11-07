## 1. Backend Implementation

- [x] 1.1 Add `get_member_counter_events` method to `OdooClient` class in `backend/odoo_client.py`
  - [x] Query `shift.counter.event` model with partner_id filter
  - [x] Filter out ignored events (ignored=False or NULL)
  - [x] Fetch fields: id, create_date, point_qty, sum_current_qty, shift_id, is_manual, name, type
  - [x] Apply limit of 50 records ordered by create_date desc
  - [x] Return list of counter event dictionaries

- [x] 1.2 Update `/api/member/<id>/history` endpoint in `backend/app.py`
  - [x] Call `odoo.get_member_counter_events(member_id)` to fetch counter events
  - [x] Create mapping of shift_id to counter events for automatic changes
  - [x] Add counter event data to shift events when shift_id matches
  - [x] Create separate events for manual counter changes (is_manual=True or no shift_id)
  - [x] Add counter events to events array with type='counter'
  - [x] Include counter_events field in JSON response for reference

- [x] 1.3 Test backend changes
  - [x] Verify counter events are fetched correctly from Odoo
  - [x] Confirm automatic counter events are linked to shifts
  - [x] Confirm manual counter events are returned as separate events
  - [x] Check error handling when counter event fetch fails

## 2. Frontend Implementation

- [x] 2.1 Update shift event card rendering in `frontend/src/App.jsx`
  - [x] Check if shift event has associated counter data
  - [x] Display counter info right-aligned: "+/-X (Total: Y)"
  - [x] Apply green styling for positive point_qty
  - [x] Apply red styling for negative point_qty
  - [x] Ensure layout accommodates counter display without breaking card design

- [x] 2.2 Add manual counter event card rendering in `frontend/src/App.jsx`
  - [x] Create case for type='counter' in event rendering switch
  - [x] Display counter event card with distinctive icon (⚖️ or 🔄)
  - [x] Show point quantity with +/- sign
  - [x] Show running total: "(Total: Y)"
  - [x] Show event name/description
  - [x] Apply green gradient for positive point_qty
  - [x] Apply red gradient for negative point_qty
  - [x] Use neutral styling for zero point_qty

- [x] 2.3 Update timeline grouping logic in `frontend/src/App.jsx`
  - [x] Ensure manual counter events are included in cycle/week grouping
  - [x] Use create_date for timeline positioning
  - [x] Maintain chronological sorting with other event types

- [x] 2.4 Add internationalization for counter events
  - [x] Add translation keys to `frontend/src/locales/en.json`
    - "counter.manual": "Manual Point Adjustment"
    - "counter.points": "Points"
    - "counter.total": "Total"
  - [x] Add French translations to `frontend/src/locales/fr.json`
    - "counter.manual": "Ajustement Manuel de Points"
    - "counter.points": "Points"
    - "counter.total": "Total"
  - [x] Use translation function for all counter-related text

## 3. Testing & Validation

- [x] 3.1 Manual testing
  - [x] Test with member who has automatic counter changes from shifts
  - [x] Test with member who has manual counter adjustments
  - [x] Test with member who has both types of counter events
  - [x] Test with member who has no counter events
  - [x] Verify positive/negative styling works correctly
  - [x] Verify counter display in shift cards is right-aligned
  - [x] Verify manual counter events appear in correct cycle/week
  - [x] Check responsive layout on different screen sizes

- [x] 3.2 Edge cases
  - [x] Test with zero point_qty counter events
  - [x] Test with very large point quantities or totals
  - [x] Test when counter event fetch fails (error handling)
  - [x] Test member with >50 counter events (pagination limit)

- [x] 3.3 Integration testing
  - [x] Verify counter events sort correctly with purchases/shifts/leaves
  - [x] Check loading states display properly
  - [x] Confirm error handling doesn't break timeline display
  - [x] Test language switching with counter events displayed

## 4. Documentation

- [x] 4.1 Update `specs/features.md` if needed
  - [x] Document counter event display behavior
  - [x] Add examples of counter event cards
  - [x] Explain automatic vs manual counter changes

- [x] 4.2 Update `specs/odoo.md` if needed
  - [x] Ensure shift.counter.event model documentation is accurate
  - [x] Document fields used and their purpose

## 5. Bug Fixes

- [x] 5.1 Fix running total calculation issue
  - [x] Remove problematic domain filter for ignored field
  - [x] Calculate running totals chronologically instead of using Odoo's sum_current_qty
  - [x] Fetch ALL counter events without limit for accurate calculation
  - [x] Aggregate multiple counter events per shift (sum point_qty values)
  - [x] Apply display limit after calculation
  - [x] Test with both ABCD and FTOP member types

- [x] 5.2 Verify fix with test members
  - [x] Test ABCD member (GHILI, Alexandre - ID 6665)
  - [x] Test FTOP member (Pollart, Sabine - ID 6338)
  - [x] Confirm running totals display correctly in both inline and manual events

- [x] 5.3 Implement separate counter type tracking
  - [x] Recognize that members have TWO separate counters (FTOP and ABCD/Standard)
  - [x] Update backend aggregation to track ftop and standard counters separately
  - [x] Calculate running totals independently for each counter type
  - [x] Process events chronologically, updating only the matching counter type
  - [x] Store both ftop_total and standard_total on each event
  - [x] Update API response to include counter type and both totals
  - [x] Update frontend to display counter type icons (⏱️ for FTOP, 📅 for ABCD)
  - [x] Display the appropriate total based on the event's counter type
  - [x] Add i18n translations for counter types (EN/FR)
  - [x] Test with member who transitioned between types (ID 6665: FTOP → ABCD)
  - [x] Verify both counter balances are correctly maintained through transition
