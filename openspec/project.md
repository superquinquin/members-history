# Project Context

## Purpose
A web application for Superquinquin cooperative supermarket to display member history, including purchases, shift participation, and attendance records. The app helps track cooperative member engagement by connecting to Odoo ERP system and visualizing purchase history and shift attendance in an intuitive timeline grouped by cycles and weeks.

## Tech Stack

**Backend:**
- Python 3.8+
- Flask 3.0.0 - Web framework
- Flask-CORS 4.0.0 - CORS support
- python-dotenv 1.0.0 - Environment configuration
- XML-RPC - Odoo API communication
- requests 2.31.0 - HTTP client
- aiohttp 3.8.0+ - Async HTTP operations (for geocoding scripts)

**Frontend:**
- React 19.1.1 - UI framework
- Vite 7.1.7 - Build tool and dev server
- Tailwind CSS 4.1.14 - Utility-first styling
- i18next 25.6.0 & react-i18next 16.0.0 - Internationalization (EN/FR)
- ESLint 9.36.0 - Linting

**Tooling:**
- devenv with Nix flakes for reproducible dev environments

## Project Conventions

### Code Style

**Python Backend:**
- Type hints required: `Optional`, `Dict`, `List`, `Any` from `typing`
- Naming conventions:
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - Descriptive names preferred
- Import order: standard library → third-party (Flask, requests) → local modules
- Error handling: try-except blocks with `print()` + `traceback.print_exc()` for debugging
- Return JSON responses with appropriate HTTP status codes
- Classes: initialize config from environment variables in `__init__`, use instance variables with type hints
- **NO COMMENTS** unless explicitly requested

**React Frontend:**
- Functional components only with React hooks (`useState`, `useEffect`, `useTranslation`)
- Naming conventions:
  - camelCase for variables and functions
  - PascalCase for components
- Import order: React imports → third-party libraries → local assets/data
- Styling: Tailwind CSS utility classes with gradient themes (purple/pink/blue)
- State management: destructured `useState` hooks, group related state
- API calls: use `fetch` with async/await in try-catch blocks
- Environment variables: access via `import.meta.env.VITE_*`
- Internationalization: use `useTranslation()` hook, call `t()` with keys from `locales/` JSON files
- **NO COMMENTS** unless explicitly requested

### Architecture Patterns

**Backend:**
- Flask application in `app.py` with route handlers
- Business logic separated into dedicated modules (e.g., `odoo_client.py`)
- OdooClient class encapsulates Odoo XML-RPC communication
- RESTful API endpoints under `/api/` prefix
- CORS enabled for cross-origin frontend requests

**Frontend:**
- Single-page application with component-based architecture
- All logic in `App.jsx` (currently monolithic)
- Data fetching on user interaction (search, member selection)
- Client-side internationalization with language toggle
- Timeline visualization grouped by cycles → weeks → events
- Base64 image handling for member profile pictures

**Data:**
- Static cycle data in `data/cycles_2025.json` for timeline grouping
- Scripts in `scripts/` for geocoding and distance calculations

### Testing Strategy
- **Backend:** No test framework configured
- **Frontend:** No test framework configured
- Manual testing via browser and API endpoints
- Health check endpoint: `GET /api/health`

### Git Workflow
- Main branch for stable code
- Feature branches for development (assumed convention)
- Commit messages should be descriptive
- `.gitignore` excludes: venv, node_modules, .env files, Python cache, build artifacts

## Domain Context

**Cooperative Supermarket Context:**
- Members participate in shifts (work schedules) organized by weekly cycles
- Cycles contain 4 weeks (A, B, C, D) with defined start/end dates
- Members make purchases tracked in Odoo POS system
- Shift states: `done` (attended), `absent` (missed), `excused` (excused absence)
- Late arrivals tracked separately with `is_late` flag

**Odoo Integration:**
- Uses `coop_membership` and `coop_shift` modules
- Member data stored in `res.partner` model with custom fields
- Purchase history from `pos.order` model
- Shift attendance from `shift.shift.attendance` model
- Authentication via XML-RPC with username/password

## Important Constraints

**Technical:**
- Backend runs on port 5001 (configurable via `FLASK_PORT`)
- Frontend dev server on port 5173 (Vite default)
- Requires active Odoo instance with XML-RPC access
- Environment variables required for both frontend and backend (see `.env.example` files)
- Base64 image data transferred directly in JSON responses

**Security:**
- Odoo credentials stored in `.env` (never commit)
- CORS configured for development (needs review for production)
- No authentication layer between frontend and backend API

**Performance:**
- Member search can be resource-intensive on large datasets
- History fetching loads all purchases and shifts (no pagination)
- Frontend processes timeline grouping client-side

## External Dependencies

**Odoo ERP System:**
- XML-RPC API at configured `ODOO_URL`
- Required models: `res.partner`, `pos.order`, `shift.shift.attendance`
- Authentication: username/password
- See `specs/odoo.md` for schema details

**Development Environment:**
- devenv with Nix for reproducible setup
- Configuration in `devenv.nix`, `devenv.yaml`, `.devenv.flake.nix`
