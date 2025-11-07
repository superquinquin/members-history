## 1. Backend Implementation
- [x] 1.1 Add `get_member_leaves()` method to `OdooClient` class in `backend/odoo_client.py`
- [x] 1.2 Fetch leaves from `shift.leave` model with state='done', include type_id name
- [x] 1.3 Update `/api/member/<id>/history` endpoint to include leaves in response
- [x] 1.4 Test backend endpoint returns leave data correctly

## 2. Frontend Data Handling
- [x] 2.1 Update API response type to include leaves array
- [x] 2.2 Add leave type to event processing in `groupEventsByCycle()`
- [x] 2.3 Create `getEventsInLeavePeriod()` helper to detect events during leave
- [x] 2.4 Add `isEventDuringLeave()` helper for individual event checking

## 3. Frontend UI Components
- [x] 3.1 Create leave banner component rendering spanning multiple weeks/cycles if needed
- [x] 3.2 Style banner with yellow background, vacation icon 🏖️, leave type and dates
- [x] 3.3 Position banners behind event cards but above timeline background
- [x] 3.4 Add visual indicator on events that occurred during leave periods
- [x] 3.5 Style shift excused/absent events differently when covered by leave

## 4. Internationalization
- [x] 4.1 Add translation keys for leave types in `frontend/src/locales/en.json`
- [x] 4.2 Add French translations in `frontend/src/locales/fr.json`
- [x] 4.3 Format leave date ranges with locale-aware formatting

## 5. Testing & Validation
- [x] 5.1 Test with members who have no leaves
- [x] 5.2 Test with members who have single leave period
- [x] 5.3 Test with members who have overlapping/consecutive leaves
- [x] 5.4 Test with members who have leaves spanning multiple cycles
- [x] 5.5 Verify leave banners display correctly across cycle boundaries
- [x] 5.6 Run frontend linter: `npm run lint` from `/frontend`
