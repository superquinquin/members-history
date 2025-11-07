<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Agent Instructions for Members History

## Subagents

### doc
**Role:** Create and update developer documentation for the project

**Capabilities:**
- Generate API documentation from code
- Update architecture and design documents
- Document code patterns, conventions, and best practices
- Create getting started guides and tutorials
- Maintain changelog and migration guides
- Document dependencies and environment setup

**Guidelines:**
- Follow project conventions from Code Style section
- Keep documentation concise and practical
- Include code examples where relevant
- Update existing docs rather than creating duplicates
- Place docs in appropriate locations (README.md for overview, specs/ for features/specs, inline for API docs)
- Use markdown format with clear headings and structure

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
