# Agent Instructions for Members History

## Commands

**Frontend (from `/frontend`):**
- Dev: `npm run dev`
- Build: `npm run build`
- Lint: `npm run lint`

**Backend (from `/backend`):**
- Run: `python app.py` (uses Flask dev server on port 5001)
- No tests configured

## Code Style

**Python Backend:**
- Use type hints (`typing` module: `Optional`, `Dict`, `List`, `Any`)
- Use `snake_case` for functions/variables
- Keep route handlers in `app.py`, business logic in separate modules like `odoo_client.py`
- Error handling: use try-except with print statements for debugging, return JSON errors with status codes
- Imports: standard library → third-party → local modules

**React Frontend:**
- Use functional components with hooks (`useState`, etc.)
- Tailwind CSS for styling (utility classes)
- camelCase for variables/functions
- No unused vars except those matching `^[A-Z_]` pattern
- ESLint configured with React Hooks rules
