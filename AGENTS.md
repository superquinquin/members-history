# Agent Instructions for Members History

## Commands

**Frontend (from `/frontend`):**
- Dev: `npm run dev` (Vite dev server)
- Build: `npm run build`
- Lint: `npm run lint`
- Preview: `npm run preview`

**Backend (from `/backend`):**
- Run: `python app.py` (Flask dev server on port 5001)
- No tests configured

## Code Style

**Python Backend:**
- Type hints required: `Optional`, `Dict`, `List`, `Any` from `typing`
- Naming: `snake_case` for functions/variables, `PascalCase` for classes
- Imports order: standard library → third-party (Flask, requests, dotenv) → local modules
- Architecture: route handlers in `app.py`, business logic in separate modules (e.g., `odoo_client.py`)
- Error handling: try-except blocks with print + traceback for debugging, return JSON errors with status codes
- Classes: use `__init__` for config from env vars, instance variables with type hints

**React Frontend:**
- Components: functional components only, hooks (`useState`, `useTranslation`)
- Styling: Tailwind CSS utility classes (e.g., `bg-gradient-to-r`, `rounded-xl`)
- Naming: camelCase for variables/functions, PascalCase for components
- Imports: React hooks first → third-party (react-i18next) → assets
- ESLint: no unused vars except matching `^[A-Z_]` pattern
- State: use destructured `useState` hooks, group related state together
- API calls: use `fetch` with async/await, handle errors in try-catch
- Env vars: access via `import.meta.env.VITE_*` for Vite
- i18n: use `useTranslation` hook, call `t()` with keys from locales files

## Specifications

- `specs/features.md`: Feature documentation (i18n, member search, profile pictures, purchase history timeline)
- `specs/odoo.md`: Odoo schema reference (coop_membership & coop_shift modules, models, fields, future features)
