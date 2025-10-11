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
- Display member details: name, address, phone
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
      "phone": "06 79 46 09 36"
    }
  ]
}
```

## Member History (Coming Soon)

### Overview
View detailed history for a selected member including:
- Purchase history
- Shift participation
- Attendance records

**Status:** Placeholder implemented, backend integration pending

**Backend Endpoint:** `GET /api/member/{member_id}/history` (stub only)
