## Why
Members' shift counter changes (point additions/deductions) are currently not visible in the history timeline, making it difficult to understand how their shift credit balance evolved over time. This information is crucial for members to track their cooperative participation status and understand point adjustments from attended/missed shifts or manual interventions.

## What Changes
- Fetch shift counter events from Odoo `shift.counter.event` model
- Display automatic counter changes (from shift attendance) inline within shift event cards
- Display manual counter changes as dedicated timeline events
- Show point quantity (+/-) and running total for all counter changes
- Apply positive/negative styling based on point direction
- Integrate counter events with existing timeline grouping by cycles and weeks

## Impact
- Affected specs: member-history
- Affected code:
  - `backend/odoo_client.py` - Add method to fetch counter events
  - `backend/app.py` - Include counter data in history API response
  - `frontend/src/App.jsx` - Render counter changes in timeline UI
