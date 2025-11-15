# FTOP Shift Timeline Analysis

**Date:** 2025-11-10  
**Purpose:** Understanding current implementation to add FTOP shift visualization

---

## Executive Summary

The member history timeline currently displays:
- ✅ Purchases (from POS)
- ✅ Standard shift attendance (done/absent/excused)
- ✅ Counter changes (FTOP and Standard counters tracked separately)
- ✅ Leave periods
- ❌ **NO visual distinction for FTOP shifts vs Standard shifts**

**Goal:** Add visual indicators to distinguish FTOP shifts from Standard ABCD shifts on the timeline.

---

## Current Timeline Implementation

### 1. Timeline Structure

**Organization:**
```
Cycles (4-week periods, gray background)
└── Weeks (A, B, C, D with colored labels)
    └── Events (cards with icons, sorted newest first)
```

**Event Types Displayed:**
1. 🛒 **Purchase** - Purple-pink gradient
2. 🎯 **Shift Attended** - Green gradient  
3. ❌ **Shift Missed** - Red gradient
4. ✓ **Shift Excused** - Blue gradient
5. ⚖️ **Manual Counter Adjustment** - Green/red based on +/-
6. 🏖️ **Leave Start** - Yellow gradient
7. 🔙 **Leave End** - Yellow gradient

### 2. Counter Movement Display

**Two Separate Counter Systems:**
- ⏱️ **FTOP Counter** - "Flying time off" / vacation shifts
- 📅 **Standard Counter** - Regular ABCD shift cycles

**Display Patterns:**

**A) In Shift Cards** (automatic counter changes):
```
Shift: Monday Morning Team A
⏱️ FTOP +2 → 10    [right-aligned, green text]
```

**B) Standalone Counter Events** (manual adjustments):
```
⚖️ Manual Point Adjustment
⏱️ FTOP +5 → 15
Manual adjustment - late arrival
```

**⚠️ KNOWN ISSUE:** Counter events are being displayed multiple times. For example, if shift 11986 has 2 counter events (+1 and -2), you see:
1. The shift with aggregated counter (-1) ✅
2. The +1 event as standalone ❌ 
3. The -2 event as standalone ❌

**Root Cause:** `backend/app.py` lines 375-395 iterate through raw `counter_events` and add them as standalone events if `is_manual=True` OR no `shift_id`. This duplicates events that were already aggregated and attached to shifts.

---

## Backend Data Structure

### Odoo Models

#### `res.partner` (Members)
```python
{
  'id': 267,
  'name': 'NIVET, Rémi',
  'shift_type': 'ftop',  # or 'standard' ← KEY FIELD
  'final_ftop_point': 10.0,
  'display_ftop_points': 10.0
}
```

#### `shift.registration` (Shift Attendance)
```python
{
  'id': 12345,
  'partner_id': 267,
  'shift_id': [11986, 'Monday Morning Team A'],  # Many2one tuple
  'date_begin': '2025-10-03 09:00:00',
  'date_end': '2025-10-03 12:00:00',
  'state': 'done',  # or 'absent', 'excused'
  'is_late': False
}
```

#### `shift.shift` (Shift Instances)
```python
{
  'id': 11986,
  'name': 'Monday Morning Team A',
  'date_begin': '2025-10-03 09:00:00',
  'week_number': 1,
  'week_name': 'A',
  'shift_template_id': [234, 'Monday Morning Template'],
  'shift_type_id': [5, 'FTOP']  # ← May indicate FTOP type
}
```

#### `shift.template` (Recurring Shifts)
```python
{
  'id': 234,
  'name': 'Monday Morning Template',
  'shift_type_id': [5, 'FTOP'],  # ← Links to shift.type
  'week_number': 1
}
```

#### `shift.counter.event` (Counter Changes)
```python
{
  'id': 67890,
  'partner_id': 267,
  'shift_id': [11986],  # Optional - links to shift
  'create_date': '2025-10-03 12:05:00',
  'point_qty': 2,  # +/- points
  'sum_current_qty': 10,  # Running total (deprecated)
  'type': 'ftop',  # or 'standard' ← Identifies counter type
  'is_manual': False,
  'name': 'Shift attendance'
}
```

### How FTOP Shifts Are Identified

**Three potential sources:**

1. **Member's shift_type** (Simplest)
   - `res.partner.shift_type` = `'ftop'` or `'standard'`
   - Indicates member's current shift system
   - **Pros:** Simple, one query
   - **Cons:** Doesn't handle members who switch systems

2. **Shift's shift_type_id** (Most accurate)
   - `shift.shift.shift_type_id` links to `shift.type` model
   - Each shift instance has its own type
   - **Pros:** Handles member transitions
   - **Cons:** Requires additional query to fetch shift types

3. **Template's shift_type_id**
   - `shift.template.shift_type_id` via `shift.shift.shift_template_id`
   - **Pros:** Accurate for template-generated shifts
   - **Cons:** Complex query, may not cover all shifts

**Recommended Approach:** Use member's `shift_type` for simplicity, with option to enhance later.

---

## Counter Calculation Logic

### Backend Processing (`backend/app.py` lines 89-233)

**Step 1: Aggregate by shift_id AND counter type**
```python
ftop_shift_map = {}      # shift_id → aggregated FTOP counter data
standard_shift_map = {}  # shift_id → aggregated Standard counter data

for counter_event in sorted_events:
    counter_type = counter_event.get('type', 'standard')
    shift_map = ftop_shift_map if counter_type == 'ftop' else standard_shift_map
    
    if shift_id in shift_map:
        shift_map[shift_id]['point_qty'] += counter_event['point_qty']
    else:
        shift_map[shift_id] = {'point_qty': counter_event['point_qty'], ...}
```

**Step 2: Calculate running totals chronologically**
```python
ftop_running_total = 0
standard_running_total = 0

for item in all_counter_items:  # Sorted by create_date
    if item['counter_type'] == 'ftop':
        ftop_running_total += item['point_qty']
    else:
        standard_running_total += item['point_qty']
    
    # Store BOTH totals at this point in time
    item['ftop_total'] = ftop_running_total
    item['standard_total'] = standard_running_total
```

**Step 3: Link to shifts**
```python
if shift_id and shift_id in shift_counter_map:
    shift_event['counter'] = shift_counter_map[shift_id]
```

**Key Insight:** Members have TWO independent counters that must be tracked separately.

---

## Frontend Architecture

### Component: `frontend/src/App.jsx` (623 lines)

**Key Helper Functions:**

```javascript
// Date formatting
formatDate(dateString)        // "Oct 4, 2025" (with year)
formatDateShort(dateString)   // "Oct 4" (without year)

// Cycle mapping (from cycles_2025.json)
getCycleAndWeekForDate(dateString) → {
  cycleNumber: 1,
  weekLetter: "A",
  cycleStartDate: "2025-01-06",
  weekStartDate: "2025-01-06",
  ...
}

// Leave detection
isEventDuringLeave(eventDate, leaves) → leave | null

// Event grouping
groupEventsByCycle(events, leaves) → [
  {
    cycleNumber: 1,
    weeks: {
      "A": { events: [...] },
      "B": { events: [...] }
    }
  }
]

// Event rendering helpers
getEventIcon()      // Returns emoji for event type
getEventBgColor()   // Returns Tailwind gradient classes
getEventTitle()     // Returns translated title
```

### Event Rendering Pattern

**Shift Event Structure:**
```jsx
<div className="relative">
  {/* Icon badge */}
  <div className="absolute -left-12 top-1 w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-500">
    🎯
  </div>
  
  {/* Event card */}
  <div className="bg-white rounded-xl p-4 shadow-md border-2 border-purple-200">
    <div className="flex justify-between items-center">
      <div className="flex items-center gap-2">
        <span className="font-semibold">Shift Attended</span>
      </div>
      <span className="text-sm text-purple-600">Oct 4, 2025</span>
    </div>
    
    <div className="text-sm text-gray-700 mt-2">
      <div className="flex items-center justify-between">
        <div>
          <span className="font-medium">Shift:</span>
          <span>Monday Morning Team A</span>
        </div>
        
        {/* Counter display */}
        {event.counter && (
          <div className="text-sm font-semibold text-green-600">
            <span>⏱️</span>
            <span className="text-xs">FTOP</span>
            <span>+2 → 10</span>
          </div>
        )}
      </div>
    </div>
  </div>
</div>
```

---

## What's Missing for FTOP Shifts

### Current State
- ✅ FTOP counter events are tracked separately
- ✅ Counter display shows FTOP vs Standard icon (⏱️ vs 📅)
- ❌ **Shifts themselves don't show if they're FTOP type**
- ❌ No visual distinction between FTOP and Standard shifts
- ❌ Member's shift_type not fetched or displayed

### Required Changes

#### Backend (`backend/`)

**1. Fetch member's shift_type**
```python
# In odoo_client.py, add to search_members_by_name()
fields = [..., 'shift_type']

# In app.py, include in history response
member_info = odoo.execute('res.partner', 'read', [member_id], ['shift_type'])
member_shift_type = member_info[0].get('shift_type', 'standard')
```

**2. Add to shift events**
```python
# In app.py, when creating shift events
shift_event = {
    'type': 'shift',
    'id': shift.get('id'),
    'date': shift.get('date_begin'),
    'shift_name': shift.get('shift_name'),
    'state': shift.get('state'),
    'is_late': shift.get('is_late', False),
    'is_ftop': member_shift_type == 'ftop',  # ← Add this
    'counter': shift_counter_map.get(shift_id)
}
```

**3. Fix counter event duplication**
```python
# In app.py, lines 375-395, only add truly manual events
if counter_events:
    for counter_event in counter_events:
        shift_id = counter_event.get('shift_id')
        if shift_id and isinstance(shift_id, list):
            shift_id = shift_id[0]
        
        is_manual = counter_event.get('is_manual', False)
        # Only add if manual AND not already attached to a shift
        if is_manual and (not shift_id or shift_id not in shift_counter_map):
            events.append({...})
```

#### Frontend (`frontend/src/`)

**1. Add FTOP indicator badge**
```jsx
{event.is_ftop && (
  <span className="text-xs bg-orange-200 text-orange-800 px-2 py-0.5 rounded-full">
    ⏱️ {t('timeline.ftopShift')}
  </span>
)}
```

**2. Update event styling**
```javascript
const getEventBgColor = () => {
  if (event.type === 'shift') {
    if (event.is_ftop) {
      // FTOP shifts: orange gradient for attended, red/blue for missed/excused
      if (event.state === 'done') return 'from-orange-500 to-amber-500'
      if (event.state === 'absent') return 'from-red-500 to-rose-500'
      if (event.state === 'excused') return 'from-blue-500 to-cyan-500'
    } else {
      // Standard shifts: green for attended, red/blue for missed/excused
      if (event.state === 'done') return 'from-green-500 to-emerald-500'
      if (event.state === 'absent') return 'from-red-500 to-rose-500'
      if (event.state === 'excused') return 'from-blue-500 to-cyan-500'
    }
  }
  // ... other event types
}
```

**3. Update event titles**
```javascript
const getEventTitle = () => {
  if (event.type === 'shift') {
    if (event.is_ftop) {
      if (event.state === 'done') return t('timeline.ftopShiftAttended')
      if (event.state === 'absent') return t('timeline.ftopShiftMissed')
      if (event.state === 'excused') return t('timeline.ftopShiftExcused')
    } else {
      if (event.state === 'done') return t('timeline.shiftAttended')
      if (event.state === 'absent') return t('timeline.shiftMissed')
      if (event.state === 'excused') return t('timeline.shiftExcused')
    }
  }
  // ... other event types
}
```

**4. Add translations**
```json
// en.json
{
  "timeline": {
    "ftopShift": "FTOP Shift",
    "ftopShiftAttended": "FTOP Shift Attended",
    "ftopShiftMissed": "FTOP Shift Missed",
    "ftopShiftExcused": "FTOP Shift Excused"
  }
}

// fr.json
{
  "timeline": {
    "ftopShift": "Créneau Vacation",
    "ftopShiftAttended": "Présence Créneau Vacation",
    "ftopShiftMissed": "Absence Créneau Vacation",
    "ftopShiftExcused": "Absence Excusée Créneau Vacation"
  }
}
```

---

## Files to Modify

### Backend
- ✏️ `backend/odoo_client.py` - Add shift_type to member queries
- ✏️ `backend/app.py` - Include is_ftop in shift events, fix counter duplication

### Frontend
- ✏️ `frontend/src/App.jsx` - Add FTOP indicators, update styling/titles
- ✏️ `frontend/src/locales/en.json` - Add FTOP translations
- ✏️ `frontend/src/locales/fr.json` - Add FTOP translations

---

## Testing Strategy

### Manual Testing
1. **Find FTOP member** - Search for member with `shift_type='ftop'`
2. **Verify FTOP indicator** - Check orange badge appears on their shifts
3. **Verify counter display** - Ensure ⏱️ icon and "FTOP" label show
4. **Verify styling** - Check orange gradient for attended FTOP shifts
5. **Test Standard member** - Ensure no FTOP indicators for standard members
6. **Test translations** - Switch language and verify French labels

### Edge Cases
- Member with no shifts
- Member with mixed FTOP/Standard shifts (if they switched)
- Shift with no counter events
- Shift with multiple counter events (verify aggregation)
- Leave period overlapping FTOP shifts

---

## Recommended Implementation Order

1. **Backend: Fetch shift_type** - Add to member queries
2. **Backend: Include in shift events** - Add `is_ftop` field
3. **Backend: Fix counter duplication** - Update event filtering logic
4. **Frontend: Add translations** - Update locale files
5. **Frontend: Add FTOP badge** - Simple conditional render
6. **Frontend: Update styling** - Modify color helper functions
7. **Frontend: Update titles** - Modify title helper function
8. **Test thoroughly** - Manual testing with FTOP and Standard members

---

## Alternative: Per-Shift Type Detection

If members can switch between FTOP and Standard systems:

**Backend:**
```python
# Fetch shift_type_id for each shift
shift_fields = ['id', 'name', 'date_begin', 'week_number', 'week_name', 'shift_type_id']
shift_results = self.models.execute_kw(...)

# Include in shift event
shift_event['shift_type_id'] = shift.get('shift_type_id')
shift_event['is_ftop'] = (
    shift.get('shift_type_id') and 
    'ftop' in str(shift.get('shift_type_id')).lower()
)
```

**Pros:** Handles member transitions accurately  
**Cons:** More complex, requires additional Odoo queries

---

## Living Documentation

Context documents created in `docs/agent/context/`:
- ✅ `project-structure.md` - Directory layout and build system
- ✅ `coding-patterns.md` - Code style and conventions
- ✅ `dependencies.md` - Libraries and external services
- ✅ `timeline-architecture.md` - Timeline implementation details

---

**End of Analysis**
