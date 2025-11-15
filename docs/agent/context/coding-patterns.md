# Coding Patterns

Last updated: 2025-11-10

## Naming Conventions

### Python Backend
- **Files**: snake_case (e.g., `odoo_client.py`, `app.py`)
- **Classes**: PascalCase (e.g., `OdooClient`)
- **Functions**: snake_case (e.g., `get_member_history`, `search_members_by_name`)
- **Variables**: snake_case (e.g., `partner_id`, `shift_counter_map`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `FLASK_PORT`)

### React Frontend
- **Files**: PascalCase for components (e.g., `App.jsx`), camelCase for utilities (e.g., `i18n.js`)
- **Components**: PascalCase (e.g., `App`)
- **Functions**: camelCase (e.g., `formatDate`, `getCycleAndWeekForDate`)
- **Variables**: camelCase (e.g., `selectedMember`, `historyEvents`)
- **Constants**: camelCase (e.g., `apiUrl`)

## Import Patterns

### Python
```python
# Standard library first
import os
from typing import Optional, Dict, List, Any

# Third-party libraries
from flask import Flask, jsonify, request
from flask_cors import CORS
import xmlrpc.client

# Local modules
from odoo_client import OdooClient
```

### React
```javascript
// React hooks first
import { useState } from 'react'

// Third-party libraries
import { useTranslation } from 'react-i18next'

// Local imports
import cyclesData from '../../data/cycles_2025.json'
```

## Error Handling

### Backend Pattern
```python
try:
    # Business logic
    results = odoo.get_member_shift_history(member_id)
    return jsonify({'events': results})
except Exception as e:
    print(f"Error fetching data: {e}")
    import traceback
    traceback.print_exc()
    return jsonify({'error': str(e)}), 500
```

**Key points:**
- Use try-except blocks for all external API calls
- Print error messages with context
- Use `traceback.print_exc()` for debugging
- Return JSON error responses with appropriate HTTP status codes
- Continue execution when possible (e.g., counter events failure doesn't block timeline)

### Frontend Pattern
```javascript
try {
  const response = await fetch(`${apiUrl}/api/member/${member.id}/history`)
  const data = await response.json()
  
  if (!response.ok) {
    throw new Error(data.error || 'Failed to fetch history')
  }
  
  setHistoryEvents(data.events || [])
} catch (err) {
  setHistoryError(err.message)
} finally {
  setHistoryLoading(false)
}
```

**Key points:**
- Use async/await for API calls
- Check `response.ok` before processing
- Provide fallback error messages
- Update loading state in finally block
- Set error state for UI display

## State Management (React)

### Pattern: Destructured useState
```javascript
const [searchName, setSearchName] = useState('')
const [members, setMembers] = useState([])
const [loading, setLoading] = useState(false)
const [error, setError] = useState(null)
```

**Key points:**
- Group related state together
- Use descriptive names (e.g., `historyLoading` vs just `loading`)
- Initialize with appropriate default values (empty array, null, false)

## API Response Patterns

### Backend Response Format
```python
# Success response
return jsonify({
    'member_id': member_id,
    'events': events,
    'leaves': leave_periods
})

# Error response
return jsonify({'error': 'Error message'}), 500
```

### Event Structure
```python
{
    'type': 'shift',  # or 'purchase', 'counter', 'leave_start', 'leave_end'
    'id': 12345,
    'date': '2025-10-03 09:00:00',
    'shift_name': 'Monday Morning Team A',
    'state': 'done',  # or 'absent', 'excused'
    'is_late': False,
    'counter': {  # Optional, only for shifts with counter events
        'point_qty': 2,
        'type': 'ftop',  # or 'standard'
        'ftop_total': 10,
        'standard_total': 5,
        'sum_current_qty': 10  # For backward compatibility
    }
}
```

## Counter Calculation Pattern

### Two-Pass Aggregation
```python
# Step 1: Aggregate counter events by shift_id AND counter type
ftop_shift_map = {}
standard_shift_map = {}

for counter_event in counter_events_sorted:
    counter_type = counter_event.get('type', 'standard')
    shift_map = ftop_shift_map if counter_type == 'ftop' else standard_shift_map
    # Aggregate...

# Step 2: Calculate running totals chronologically
ftop_running_total = 0
standard_running_total = 0

for item in all_counter_items:
    if item['counter_type'] == 'ftop':
        ftop_running_total += item['point_qty']
    else:
        standard_running_total += item['point_qty']
    
    # Store both totals at this point in time
    item['ftop_total'] = ftop_running_total
    item['standard_total'] = standard_running_total
```

**Key insight:** Members have TWO separate counters (ftop and standard) that must be tracked independently.

## Date Formatting Patterns

### Frontend Date Helpers
```javascript
// Full date with year (for events)
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat(i18n.language, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(date)
}

// Short date without year (for cycle ranges)
const formatDateShort = (dateString) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat(i18n.language, {
    month: 'short',
    day: 'numeric'
  }).format(date)
}
```

**Key points:**
- Use `Intl.DateTimeFormat` for locale-aware formatting
- Respect `i18n.language` for internationalization
- Different formats for different contexts

## Timeline Grouping Pattern

### Cycle and Week Organization
```javascript
const groupEventsByCycle = (events, leaves) => {
  const cycles = {}
  
  events.forEach(event => {
    const cycleInfo = getCycleAndWeekForDate(event.date)
    if (!cycleInfo) return
    
    const cycleKey = `cycle-${cycleInfo.cycleNumber}`
    
    // Initialize cycle structure
    if (!cycles[cycleKey]) {
      cycles[cycleKey] = {
        cycleNumber: cycleInfo.cycleNumber,
        startDate: cycleInfo.cycleStartDate,
        endDate: cycleInfo.cycleEndDate,
        weeks: {},
        leaves: [],
        allEvents: []
      }
    }
    
    // Add to appropriate week
    const weekKey = cycleInfo.weekLetter
    if (!cycles[cycleKey].weeks[weekKey]) {
      cycles[cycleKey].weeks[weekKey] = {
        weekLetter: weekKey,
        startDate: cycleInfo.weekStartDate,
        endDate: cycleInfo.weekEndDate,
        events: []
      }
    }
    
    cycles[cycleKey].weeks[weekKey].events.push(event)
  })
  
  return Object.values(cycles).sort((a, b) => b.cycleNumber - a.cycleNumber)
}
```

**Key points:**
- Use local calendar data (`cycles_2025.json`) for week assignment
- Independent of Odoo shift data
- Nested structure: cycles → weeks → events
- Sort newest first (reverse chronological)

## Styling Patterns

### Tailwind CSS Utilities
```jsx
// Gradient backgrounds
className="bg-gradient-to-r from-purple-600 to-pink-600"

// Conditional styling based on state
className={`
  p-5 rounded-xl cursor-pointer transition-all duration-200 
  ${selectedMember?.id === member.id
    ? 'bg-gradient-to-r from-purple-100 to-pink-100 border-2 border-purple-400'
    : 'bg-white border-2 border-purple-200 hover:border-purple-300'
  }
`}

// Dynamic color based on event type
const getEventBgColor = () => {
  if (event.type === 'counter') {
    if (event.point_qty > 0) return 'from-green-500 to-emerald-500'
    if (event.point_qty < 0) return 'from-red-500 to-rose-500'
    return 'from-gray-500 to-slate-500'
  }
  // ...
}
```

**Key points:**
- Use Tailwind utility classes
- Gradient theme: purple-pink throughout
- Conditional styling with template literals
- Helper functions for complex logic

## Type Hints (Python)

```python
from typing import Optional, Dict, List, Any

def get_member_shift_history(self, partner_id: int, limit: int = 50) -> List[Dict]:
    # Implementation
    return results

def execute(self, model: str, method: str, *args, **kwargs) -> Any:
    # Implementation
    return result
```

**Key points:**
- Use type hints for all function parameters and return values
- Import types from `typing` module
- Use `Any` for dynamic/unknown types
- Use `Optional[T]` for nullable values

## Internationalization Pattern

```javascript
// In component
const { t, i18n } = useTranslation()

// Simple translation
<h1>{t('app.title')}</h1>

// Translation with interpolation
<h2>{t('history.title', { name: selectedMember.name })}</h2>

// Access current language
const currentLang = i18n.language

// Change language
i18n.changeLanguage('fr')
```

**Key points:**
- Use `useTranslation` hook
- Translation keys use dot notation (e.g., `'timeline.shiftAttended'`)
- Support interpolation with named parameters
- All user-facing text must be translated
