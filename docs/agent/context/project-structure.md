# Project Structure

Last updated: 2025-11-10

## Directory Layout
```
members-history/
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application with routes
│   ├── odoo_client.py      # Odoo XML-RPC client wrapper
│   ├── odoo_schema.sql     # Database schema reference
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
├── frontend/               # React + Vite SPA
│   ├── src/
│   │   ├── App.jsx         # Main application component (timeline UI)
│   │   ├── main.jsx        # React entry point
│   │   ├── i18n.js         # i18next configuration
│   │   ├── locales/        # Translation files (en.json, fr.json)
│   │   └── assets/         # Static assets
│   ├── public/             # Public assets
│   ├── index.html          # HTML entry point
│   ├── vite.config.js      # Vite configuration
│   ├── package.json        # Node dependencies
│   └── .env.example        # Environment variables template
├── data/                   # Static data files
│   └── cycles_2025.json    # Shift cycle calendar data
├── scripts/                # Utility scripts (geocoding, distance calc)
├── specs/                  # Feature specifications
│   ├── features.md         # Feature documentation
│   ├── odoo.md            # Odoo schema reference
│   └── geocoding.md       # Geocoding specs
├── openspec/              # OpenSpec change management
│   ├── specs/             # Current specifications
│   ├── changes/           # Change proposals
│   │   └── archive/       # Completed changes
│   ├── AGENTS.md          # Agent instructions
│   └── project.md         # Project overview
└── docs/                  # Documentation
    └── agent/
        └── context/       # Living documentation for AI agents
```

## Key Files

### Backend
- **`app.py`** - Flask application entry point
  - Routes: `/api/health`, `/api/odoo/test-connection`, `/api/members/search`, `/api/member/<id>/history`
  - Handles counter event aggregation and running total calculation
  - Combines data from multiple Odoo models
  
- **`odoo_client.py`** - Odoo XML-RPC client
  - Methods: `search_members_by_name()`, `get_member_purchase_history()`, `get_member_shift_history()`, `get_member_leaves()`, `get_member_counter_events()`
  - Handles authentication and API calls to Odoo
  
- **`odoo_schema.sql`** - PostgreSQL schema dump
  - Reference for Odoo database structure
  - Key tables: `res_partner`, `pos_order`, `shift_registration`, `shift_shift`, `shift_counter_event`, `shift_leave`

### Frontend
- **`src/App.jsx`** - Main React component (623 lines)
  - Timeline rendering with cycle-based grouping
  - Event type handling: purchases, shifts, leaves, counter changes
  - Helper functions for date formatting, cycle mapping, leave detection
  - State management for search, member selection, history loading
  
- **`src/i18n.js`** - Internationalization setup
  - Supports English and French
  - Uses react-i18next
  
- **`src/locales/*.json`** - Translation files
  - All UI text is internationalized
  - Counter-specific translations: ftop vs standard

### Data
- **`data/cycles_2025.json`** - Shift cycle calendar
  - Defines 4-week cycles with weeks A, B, C, D
  - Used for timeline grouping and week letter assignment
  - Independent of Odoo shift data

## Build System
- **Backend**: Flask dev server (port 5001)
  - Run: `python app.py`
  - No build step required
  
- **Frontend**: Vite (React)
  - Dev: `npm run dev` (port 5173)
  - Build: `npm run build` → `dist/`
  - Preview: `npm run preview`
  - Lint: `npm run lint`

## Environment Configuration
- Backend: `.env` file with `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`, `FLASK_PORT`
- Frontend: `.env` file with `VITE_API_URL` (defaults to http://localhost:5001)

## External Dependencies
- **Odoo**: XML-RPC API connection to AwesomeFoodCoops Odoo instance
- **Modules**: `coop_membership` and `coop_shift` (see specs/odoo.md)
