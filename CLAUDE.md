# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Members History is a web application for the Superquinquin cooperative supermarket that displays member purchase history, shift participation, and attendance records. The application connects to an Odoo ERP instance via XML-RPC to fetch member data.

**Tech Stack:**
- Backend: Flask (Python 3.11) with XML-RPC client for Odoo
- Frontend: React 19 + Vite with Tailwind CSS and i18next
- Development: devenv (Nix-based) for reproducible environment

## Development Environment

The project uses **devenv** for environment management. All dependencies and services are configured in `devenv.nix`.

### Starting the Application

```bash
# Start both backend and frontend
devenv up

# Or start services individually
cd backend && python app.py    # Backend on http://localhost:5001
cd frontend && npm run dev      # Frontend on http://localhost:5173
```

### Environment Configuration

Before running, configure environment variables:

```bash
# Backend configuration
cp backend/.env.example backend/.env
# Edit backend/.env with Odoo credentials (ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

# Frontend configuration
cp frontend/.env.example frontend/.env
# Edit frontend/.env with VITE_API_URL (default: http://localhost:5001)
```

## Common Development Commands

### Backend (Python/Flask)

```bash
cd backend

# Run the Flask server
python app.py

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run a single test file
pytest tests/test_member_history_api.py

# Run a specific test
pytest tests/test_member_history_api.py::TestMemberHistoryAPI::test_counter_aggregation
```

### Frontend (React/Vite)

```bash
cd frontend

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Lint code
npm run lint
```

### Scripts (Geocoding Utilities)

```bash
cd scripts

# Geocode all worker members
python geocode_members.py

# Geocode with custom options
python geocode_members.py --limit 100 --format both --debug

# Calculate distances from store location
python calculate_distances.py

# Plot distance distribution
python plot_distance_distribution.py
```

## Architecture

### Backend Structure

**Core Components:**
- `app.py` - Flask application with API endpoints
- `odoo_client.py` - Odoo XML-RPC client wrapper

**Key Endpoints:**
- `GET /api/health` - Health check
- `GET /api/odoo/test-connection` - Test Odoo connection
- `GET /api/members/search?name=<name>` - Search members by name
- `GET /api/member/<member_id>/history` - Get member timeline (purchases, shifts, counter events, leaves)

**Odoo Integration:**
The application uses XML-RPC to communicate with Odoo. The `OdooClient` class handles authentication and provides methods to fetch data from various Odoo models:
- `res.partner` - Member information
- `pos.order` - Purchase history
- `shift.registration` - Shift registrations
- `shift.shift` - Shift details
- `shift.leave` - Leave periods
- `shift.counter.event` - Counter events (points system)

### Member Counter System

The application implements a **dual-counter system** for tracking member shift participation:

1. **Standard Counter (ABCD)** - For regular weekly shifts
2. **FTOP Counter (Volant)** - For flexible/on-demand shifts

**Counter Aggregation Logic** (in `app.py:141-323`):
- Counter events are aggregated by shift_id AND counter type
- Events are sorted chronologically to calculate running totals
- Both counter totals are tracked for each event (ftop_total and standard_total)
- Manual counter adjustments (no shift_id) are preserved as separate events

**Shift Type Determination** (in `app.py:98-138`):
- Primary: Uses `shift.shift_type_id` field from Odoo
- Fallback: Uses counter event type if shift_type_id missing
- Returns 'ftop', 'standard', or 'unknown'

**Important:** FTOP shifts use the counter event date (when shift was closed) instead of shift.date_begin for timeline display.

### Frontend Structure

The frontend is a single-page React application (`src/App.jsx`) with:

**Core Features:**
- Member search interface
- Timeline view grouped by cycles and weeks
- Event cards for purchases, shifts, counter events, and leaves
- Leave period overlays (shows if shift absence was during leave)
- Dual-counter display (FTOP vs Standard)
- Bilingual support (English/French) via react-i18next

**Data Flow:**
1. User searches for member by name
2. Backend queries Odoo and returns member list
3. User selects member
4. Frontend fetches member history from `/api/member/<id>/history`
5. Events are grouped by cycle and week using `data/cycles_2025.json`
6. Timeline renders with visual indicators for event types and states

**Cycle/Week System:**
- Timeline is organized by cycles (e.g., Cycle 1, 2, 3...)
- Each cycle has 4 weeks (A, B, C, D)
- Mapping defined in `data/cycles_2025.json`

### Testing

**Backend Tests:**
- Located in `backend/tests/`
- Use pytest with configuration in `backend/pytest.ini`
- Key test files:
  - `test_member_history_api.py` - API endpoint tests
  - `test_determine_shift_type.py` - Shift type logic tests
  - `conftest.py` - Shared fixtures
  - `mock_data.py` - Test data

**Frontend Tests:**
- Located in `frontend/src/tests/`
- Use Vitest with React Testing Library
- Run with `npm test` or `npm run test:ui`

## Important Implementation Details

### Shift Type Detection

When working with shift-related code, understand that shift type determination uses a hybrid approach:
1. First checks `shift.shift_type_id` from the shift record
2. Falls back to counter event type only if shift_type_id is missing
3. This ensures FTOP (volant) shifts are correctly identified vs standard ABCD shifts

### Counter Event Aggregation

The counter aggregation logic (lines 159-323 in `app.py`) is complex:
- Multiple counter events can be associated with a single shift
- Events must be aggregated by BOTH shift_id AND counter type (ftop vs standard)
- Running totals must be calculated chronologically across all events
- Manual adjustments (no shift_id) need special handling

When modifying this logic, maintain the separation between ftop and standard counters throughout the pipeline.

### Leave Period Handling

Leave periods affect shift display:
- Shifts marked as absent/excused during a leave show differently in the UI
- The frontend checks if event date falls within any leave period
- This is purely visual - backend doesn't modify the data based on leaves

### Geocoding Scripts

The `scripts/` directory contains utilities for geocoding member addresses using the French government API. These are standalone scripts that:
- Fetch worker member addresses from Odoo (no personal data beyond ID and address)
- Geocode using https://data.geopf.fr/geocodage
- Respect rate limits (40-50 req/s)
- Output JSON/CSV with coordinates

These scripts are separate from the main application and used for data analysis purposes.

## Odoo Membership System Specification

**For comprehensive documentation about how the Odoo membership and shift systems work, see:**

📖 **[specs/MEMBERSHIP_SYSTEM_SPEC.md](specs/MEMBERSHIP_SYSTEM_SPEC.md)** - Complete reference for:
- All Odoo models and their fields (res.partner, shift.*, pos.order, etc.)
- Member types, states, and workflows
- Dual-counter system (Standard ABCD vs FTOP)
- Point calculation rules and holiday relief system
- Leave system mechanics and template registration
- Shift exchange system for ABCD members
- Make-up shift logic and counter assignment rules
- Business rules, thresholds, and state transitions

📋 **[specs/KNOWLEDGE_GAPS.md](specs/KNOWLEDGE_GAPS.md)** - Documents areas needing clarification

**Quick Reference - Key Concepts:**

**Dual-Counter System:**
- Standard ABCD members use **standard counter** for regular/make-up shifts (when counter < 0)
- Standard ABCD members use **FTOP counter** for extra shifts (when counter >= 0)
- FTOP members use **FTOP counter** exclusively

**Point Rules:**
- Attended shift: **+1 point**
- Missed shift: **-2 points** (with holiday relief: +1 or +2 depending on configuration)
- Excused shift: **0 points** (no counter event created)
- FTOP cycle deduction: **-1 point** every cycle (automatic)

**Counter Thresholds (Standard ABCD):**
- `up_to_date`: counter == 0
- `alert`: counter < 0 (first cycle)
- `suspended`: counter < 0 after one cycle in alert (shopping blocked)
- `delay`: Temporary shopping privileges during make-up period

**Counter Thresholds (FTOP):**
- `up_to_date`: counter >= 0 (can be positive)
- Then same alert → suspended → delay progression when negative

**Database Models (Odoo):**

The application reads from these Odoo models (all read-only via XML-RPC):
- `res.partner` - Members/contacts
- `pos.order` - Point of sale orders
- `shift.registration` - Individual shift registrations
- `shift.shift` - Shift instances
- `shift.template` - Recurring shift templates
- `shift.template.registration` - Template assignments
- `shift.type` - Shift categories (FTOP vs Standard)
- `shift.leave` - Leave periods
- `shift.leave.type` - Types of leave
- `shift.counter.event` - Counter point adjustments
- `shift.holiday` - Holiday relief periods ("assouplissement de présence")
