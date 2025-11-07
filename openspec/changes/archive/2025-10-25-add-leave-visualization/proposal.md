## Why
Members need to see when they were on leave to understand gaps in their shift participation history. Leave periods provide important context for why shifts may have been excused or missed, and help members track their vacation/absence patterns over time.

## What Changes
- Add leave period visualization as yellow banner bars spanning the full duration on the timeline
- Fetch leave data from Odoo `shift.leave` model (done leaves only)
- Display leave type and date range within the banner
- Show purchases and shifts that occurred during leave periods
- Visually indicate when shift absences were covered by leave

## Impact
- Affected specs: member-history
- Affected code:
  - `backend/odoo_client.py` - Add method to fetch member leaves
  - `backend/app.py` - Include leaves in history endpoint response
  - `frontend/src/App.jsx` - Render leave banners in timeline, detect events during leave periods
  - `frontend/src/locales/en.json` - Add leave-related translation keys
  - `frontend/src/locales/fr.json` - Add French translations for leaves
