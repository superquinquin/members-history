# Timeline Architecture

Last updated: 2025-11-10

## Overview

The member history timeline displays events (purchases, shifts, leaves, counter changes) organized by 4-week cycles and weeks within cycles. This document details the current implementation architecture.

## Data Flow

```
Odoo Database
    ↓
Backend (app.py + odoo_client.py)
    ↓ JSON API
Frontend (App.jsx)
    ↓
Timeline UI (Cycles → Weeks → Events)
```

## Backend Architecture

### Data Sources (Odoo Models)

1. **`pos.order`** - Purchase history
   - Fields: `id`, `date_order`, `name`, `pos_reference`
   - Filter: `state='done'`, `partner_id=member_id`
   - Limit: 50 most recent

2. **`shift.registration`** - Shift attendance
   - Fields: `id`, `date_begin`, `date_end`, `state`, `shift_id`, `is_late`
   - Filter: `state in ['done', 'absent', 'excused']`, `partner_id=member_id`
   - Limit: 50 most recent
   - Additional fetch from `shift.shift` for shift name

3. **`shift.leave`** - Leave periods
   - Fields: `id`, `start_date`, `stop_date`, `type_id`, `state`
   - Filter: `state='done'`, `partner_id=member_id`
   - No limit

4. **`shift.counter.event`** - Counter changes
   - Fields: `id`, `create_date`, `point_qty`, `sum_current_qty`, `shift_id`, `is_manual`, `name`, `type`
   - Filter: `partner_id=member_id`
   - **No limit** (all events needed for accurate running totals)
   - Order: `create_date asc` for calculation

### Counter Event Processing

**Key Insight:** Members have TWO separate counters:
- **FTOP counter** (`type='ftop'`) - For "flying time off" / vacation shifts
- **Standard counter** (`type='standard'`) - For regular ABCD shift cycles

**Processing Steps:**

1. **Aggregate by shift_id AND counter type**
   ```python
   ftop_shift_map = {}      # shift_id → counter data for FTOP
   standard_shift_map = {}  # shift_id → counter data for Standard
   ```

2. **Calculate running totals chronologically**
   ```python
   ftop_running_total = 0
   standard_running_total = 0
   
   for item in sorted_items:
       if item['counter_type'] == 'ftop':
           ftop_running_total += item['point_qty']
       else:
           standard_running_total += item['point_qty']
       
       # Store BOTH totals at this point in time
       item['ftop_total'] = ftop_running_total
       item['standard_total'] = standard_running_total
   ```

3. **Link to shifts**
   - Counter events with `shift_id` → attached to shift event
   - Counter events without `shift_id` or `is_manual=True` → standalone timeline events

### API Response Structure

```json
{
  "member_id": 267,
  "events": [
    {
      "type": "shift",
      "id": 12345,
      "date": "2025-10-03 09:00:00",
      "shift_name": "Monday Morning Team A",
      "state": "done",
      "is_late": false,
      "counter": {
        "point_qty": 2,
        "type": "ftop",
        "ftop_total": 10,
        "standard_total": 5,
        "sum_current_qty": 10
      }
    },
    {
      "type": "counter",
      "id": 67890,
      "date": "2025-10-01 14:30:00",
      "point_qty": -2,
      "counter_type": "standard",
      "ftop_total": 8,
      "standard_total": 3,
      "name": "Manual adjustment - late arrival"
    }
  ],
  "leaves": [
    {
      "id": 111,
      "start_date": "2025-09-15",
      "stop_date": "2025-09-22",
      "leave_type": "Vacation",
      "state": "done"
    }
  ]
}
```

## Frontend Architecture

### Component Structure

**Single Component:** `App.jsx` (623 lines)
- Search UI
- Member selection
- Timeline rendering
- All helper functions

**State Management:**
```javascript
// Search state
const [searchName, setSearchName] = useState('')
const [members, setMembers] = useState([])
const [loading, setLoading] = useState(false)
const [error, setError] = useState(null)

// Selected member state
const [selectedMember, setSelectedMember] = useState(null)
const [historyEvents, setHistoryEvents] = useState([])
const [historyLoading, setHistoryLoading] = useState(false)
const [historyError, setHistoryError] = useState(null)
const [leaves, setLeaves] = useState([])
```

### Timeline Rendering Pipeline

1. **Fetch data** → `historyEvents` and `leaves` state
2. **Group by cycles** → `groupEventsByCycle(historyEvents, leaves)`
3. **Render cycles** → Nested structure: Cycle → Weeks → Events
4. **Event cards** → Type-specific rendering with icons, colors, details

### Key Helper Functions

#### Date Formatting
```javascript
formatDate(dateString)        // "Oct 4, 2025" (with year)
formatDateShort(dateString)   // "Oct 4" (without year)
```

#### Cycle Mapping
```javascript
getCycleAndWeekForDate(dateString) → {
  cycleNumber: 1,
  cycleStartDate: "2025-01-06",
  cycleEndDate: "2025-02-02",
  weekLetter: "A",
  weekStartDate: "2025-01-06",
  weekEndDate: "2025-01-12"
}
```

#### Leave Detection
```javascript
isEventDuringLeave(eventDate, leaves) → leave | null
```

#### Grouping
```javascript
groupEventsByCycle(events, leaves) → [
  {
    cycleNumber: 1,
    startDate: "2025-01-06",
    endDate: "2025-02-02",
    weeks: {
      "A": { weekLetter: "A", events: [...] },
      "B": { weekLetter: "B", events: [...] }
    }
  }
]
```

### Event Type Rendering

Each event type has:
- **Icon**: Emoji representing the event (🛒, 🎯, ❌, ✓, ⚖️, 🏖️, 🔙)
- **Color**: Gradient background for icon badge
- **Border**: Card border color
- **Details**: Type-specific information display

#### Shift Events
```jsx
<div className="flex items-center justify-between gap-2">
  <div className="flex items-center gap-2">
    <span className="font-medium">Shift:</span>
    <span>{event.shift_name}</span>
  </div>
  {event.counter && (
    <div className="text-sm font-semibold">
      <span>{event.counter.type === 'ftop' ? '⏱️' : '📅'}</span>
      <span>{event.counter.type === 'ftop' ? 'FTOP' : 'ABCD'}</span>
      <span>{event.counter.point_qty > 0 ? '+' : ''}{event.counter.point_qty}</span>
      <span>→ {event.counter.type === 'ftop' ? event.counter.ftop_total : event.counter.standard_total}</span>
    </div>
  )}
</div>
```

#### Counter Events (Manual)
```jsx
<div className="text-sm text-gray-700 mt-2">
  <div className="flex items-center gap-2 mb-1">
    <span className="text-lg">{event.counter_type === 'ftop' ? '⏱️' : '📅'}</span>
    <span className="text-sm font-semibold">
      {event.counter_type === 'ftop' ? 'FTOP' : 'ABCD'}
    </span>
    <span className="text-2xl font-bold">
      {event.point_qty > 0 ? '+' : ''}{event.point_qty}
    </span>
    <span className="text-gray-500">
      → {event.counter_type === 'ftop' ? event.ftop_total : event.standard_total}
    </span>
  </div>
  {event.name && <div className="text-xs">{event.name}</div>}
</div>
```

### Styling System

**Theme:** Purple-pink gradient throughout

**Color Mapping:**
- **Purchases**: Purple-pink gradient (`from-purple-500 to-pink-500`)
- **Shift attended**: Green gradient (`from-green-500 to-emerald-500`)
- **Shift missed**: Red gradient (`from-red-500 to-rose-500`)
- **Shift excused**: Blue gradient (`from-blue-500 to-cyan-500`)
- **Counter positive**: Green gradient
- **Counter negative**: Red gradient
- **Leave events**: Yellow gradient (`from-yellow-500 to-amber-500`)
- **During leave**: Grayed out (`from-gray-400 to-gray-500`)

**Week Letter Colors:**
- A: Blue (`text-blue-600`)
- B: Green (`text-green-600`)
- C: Yellow (`text-yellow-600`)
- D: Purple (`text-purple-600`)

### Layout Structure

```
Cycle Container (gray background)
├── Cycle Header (fixed 112px width)
│   ├── Cycle Number
│   ├── Start Date (short)
│   └── End Date (short)
└── Weeks Container
    └── Week (vertical timeline segment)
        ├── Week Letter (large, colored, -left-24)
        ├── Timeline Line (vertical, purple-pink gradient)
        └── Event Cards (stacked, space-y-6)
            ├── Icon Badge (circular, -left-12)
            └── Event Card (white, bordered, hover effects)
```

## Current Limitations

1. **Single component**: All logic in one 623-line file
2. **No tests**: No unit or integration tests
3. **No caching**: Every member selection fetches fresh data
4. **No pagination**: Limited to 50 events per type
5. **No filtering**: Can't filter by event type or date range
6. **No search within history**: Can't search events for selected member

## Extension Points for FTOP Shifts

### Backend Changes Needed
1. Identify FTOP shifts in `shift.registration` or `shift.shift`
   - Check `shift_type` field on `res.partner`
   - Check `shift_type_id` on `shift.shift` or `shift.template`
   
2. Add FTOP indicator to shift events
   - Include `is_ftop` boolean in shift event response
   - Or include `shift_type` field

### Frontend Changes Needed
1. Add FTOP visual indicator to shift cards
   - Icon: ⏱️ (already used for FTOP counter)
   - Badge or label: "FTOP Shift"
   - Different styling (e.g., orange gradient instead of green/red)

2. Update event rendering logic
   - Check `is_ftop` or `shift_type` field
   - Apply FTOP-specific styling
   - Show FTOP-specific details

3. Add translations
   - `timeline.ftopShift`: "FTOP Shift"
   - `timeline.ftopShiftAttended`: "FTOP Shift Attended"
   - etc.

## Data Sources for FTOP Identification

### Option 1: Member's shift_type
```python
# In odoo_client.py, when fetching member
member = self.search_read('res.partner', [('id', '=', partner_id)], ['shift_type'])
# shift_type can be 'ftop' or 'standard'
```

### Option 2: Shift template's shift_type_id
```python
# In shift.shift model, there's a shift_type_id field
# Need to fetch this when getting shift details
shift_fields = ['id', 'name', 'date_begin', 'week_number', 'week_name', 'shift_type_id']
```

### Option 3: Check shift.template
```python
# shift.template has shift_type_id field
# When fetching shift.shift, also fetch related template's type
```

## Recommended Approach

1. **Fetch member's shift_type** when loading history
2. **Include in shift events** as `member_shift_type` field
3. **For each shift**, check if it's an FTOP shift:
   - If member is FTOP type → all their shifts are FTOP shifts
   - Or check shift's own type if available
4. **Display accordingly** with FTOP styling and labels

This approach is simple and doesn't require complex Odoo queries.
