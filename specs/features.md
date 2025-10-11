# Features

## Internationalization (i18n)

### Overview
The application supports multiple languages with real-time language switching. Currently supported languages:
- English (en)
- French (fr)

### Implementation Details

**Library:** react-i18next + i18next

**Files:**
- `frontend/src/i18n.js` - Configuration and initialization
- `frontend/src/locales/en.json` - English translations
- `frontend/src/locales/fr.json` - French translations

**Features:**
- Automatic language detection and persistence in localStorage
- Language switcher button in header (🇬🇧 EN / 🇫🇷 FR)
- All UI text is translated including:
  - Navigation and headers
  - Form labels and placeholders
  - Button text and loading states
  - Error messages
  - Empty states and help text
  - Dynamic content with interpolation (e.g., "History for {name}")

**Usage:**
```javascript
import { useTranslation } from 'react-i18next'

function Component() {
  const { t, i18n } = useTranslation()
  
  // Simple translation
  return <h1>{t('app.title')}</h1>
  
  // Translation with interpolation
  return <p>{t('history.title', { name: memberName })}</p>
  
  // Change language
  i18n.changeLanguage('fr')
}
```

**Adding New Languages:**
1. Create new JSON file in `frontend/src/locales/` (e.g., `es.json`)
2. Add language resource to `frontend/src/i18n.js`:
   ```javascript
   import es from './locales/es.json'
   
   resources: {
     en: { translation: en },
     fr: { translation: fr },
     es: { translation: es }
   }
   ```
3. Update language switcher UI in `App.jsx`

### Translation Keys Structure

```json
{
  "app": {
    "title": "Application title",
    "subtitle": "Application subtitle"
  },
  "search": {
    "label": "Search form label",
    "placeholder": "Input placeholder",
    "button": "Search button text",
    "searching": "Loading state text"
  },
  "results": {
    "title": "Results section title",
    "count": "Results count (supports {{count}} interpolation)",
    "noResults": "Empty state title",
    "noResultsHint": "Empty state hint"
  },
  "history": {
    "title": "History title (supports {{name}} interpolation)",
    "memberId": "Member ID label",
    "comingSoon": "Coming soon message",
    "comingSoonDetails": "Coming soon details"
  },
  "error": {
    "label": "Error label"
  },
  "language": {
    "switch": "Switch language tooltip",
    "en": "English",
    "fr": "Français"
  }
}
```

## Member Search

### Overview
Search for cooperative members by name with real-time results from the Odoo backend.

**Backend Endpoint:** `GET /api/members/search?name={query}`

**Features:**
- Case-insensitive partial name matching
- Display member details: name, address, phone, profile picture
- Profile picture display with fallback
- Click to select member for detailed history view
- Loading states and error handling
- Empty state guidance

**Response Format:**
```json
{
  "members": [
    {
      "id": 267,
      "name": "NIVET, Rémi",
      "address": "233 rue nationale, 59800, Lille",
      "phone": "06 79 46 09 36",
      "image": "base64_encoded_string_or_null"
    }
  ]
}
```

### Profile Pictures

**Implementation:**
- Profile pictures are fetched from Odoo `res.partner` model fields: `image_small`, `image_medium`, or `image`
- Images are base64-encoded JPEG/PNG data
- Frontend displays images as circular avatars (64x64px) with border styling
- **Fallback:** When no image is available, displays gradient circle with member initials
  - Initials extracted from name (e.g., "NIVET, Rémi" → "NR")
  - Gradient background: purple-to-pink matching app theme

**Backend Fields:**
- `backend/odoo_client.py:55` requests `image`, `image_small`, and `image_medium` fields
- `backend/app.py:66-71` prioritizes `image_small` for performance, falls back to `image_medium` or `image`
- Returns base64 string in `image` field of API response

**Frontend Display:**
- `frontend/src/App.jsx` helper functions:
  - `getImageSrc(imageData)` - Converts base64 to data URL (`data:image/png;base64,{data}`)
  - `getInitials(name)` - Extracts initials for fallback avatar
- Circular avatar styling with responsive layout
- Consistent sizing and border matching app theme

## Member History

### Overview
View member activity as a vertical timeline of events, ordered from newest to oldest.

**Backend Endpoint:** `GET /api/member/{member_id}/history`

**Implemented Event Types:**

#### 1. Purchase in Store
Shows every time the member made a purchase at the cooperative store.

**Data Source:** Odoo `pos.order` model
- Filters: `state = 'done'` and `partner_id = member_id`
- Fields: `id`, `date_order`, `name`, `pos_reference`
- Sorted: Newest to oldest (by `date_order desc`)
- Limit: 50 most recent purchases

**Display:**
- Icon: 🛒
- Color: Purple-pink gradient
- Shows: Purchase reference/order number

#### 2. Shift Participation
Shows member participation in cooperative work shifts.

**Data Source:** Odoo `shift.registration` model
- Filters: `state in ['done', 'absent', 'excused']` and `partner_id = member_id`
- Fields: `id`, `date_begin`, `date_end`, `state`, `shift_id`, `is_late`
- Additional fetch from `shift.shift` model for shift name
- Sorted: Newest to oldest (by `date_begin desc`)
- Limit: 50 most recent shift registrations

**Display:**
- **Shift Attended** (`state='done'`):
  - Icon: 🎯
  - Color: Green gradient
  - Shows: Shift name, date, and "Late" indicator if `is_late=true`
- **Shift Missed** (`state='absent'`):
  - Icon: ❌
  - Color: Red gradient
  - Shows: Shift name and date
- **Shift Excused** (`state='excused'`):
  - Icon: ✓
  - Color: Blue gradient
  - Shows: Shift name and date

**Response Format:**
```json
{
  "member_id": 267,
  "events": [
    {
      "type": "purchase",
      "id": 302602,
      "date": "2025-10-04 10:33:09",
      "reference": "Commande 07291-004-0043"
    },
    {
      "type": "shift",
      "id": 12345,
      "date": "2025-10-03 09:00:00",
      "shift_name": "Monday Morning Team A",
      "state": "done",
      "is_late": false
    }
  ]
}
```

### Timeline UI

**Implementation:**
- Vertical timeline with gradient line (purple to pink)
- Event cards with type-specific icons and colors
- Date formatting: Always displays real dates (e.g., "Oct 4, 2025" or "4 oct. 2025")
  - Uses `Intl.DateTimeFormat` for locale-aware formatting
- Events sorted by date (newest to oldest)
- Mixed event types displayed in chronological order
- Loading, error, and empty states
- Fully internationalized (EN/FR)

**Frontend Components:**
- `frontend/src/App.jsx`:
  - Timeline rendering with event cards
  - `formatDate()` helper for locale-aware date display
  - Dynamic icon and color based on event type and state
  - Automatic history fetch when member is selected
  - Conditional rendering of event-specific details

**Styling:**
- Purple-pink gradient theme throughout
- Circular icon badges with type-specific gradients
- White event cards with purple borders
- Hover effects and shadows
- Responsive layout

**Backend Implementation:**
- `backend/odoo_client.py`:
  - `get_member_purchase_history()` - Fetches POS orders
  - `get_member_shift_history()` - Fetches shift registrations with shift details
- `backend/app.py`:
  - `/api/member/<id>/history` - Combines and sorts all event types
