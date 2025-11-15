# Dependencies

Last updated: 2025-11-10

## Runtime Dependencies

### Backend (Python)
- **Flask** (Web framework)
  - Lightweight WSGI web application framework
  - Used for REST API endpoints
  
- **flask-cors** (CORS support)
  - Handles Cross-Origin Resource Sharing
  - Allows frontend to call backend API
  
- **python-dotenv** (Environment variables)
  - Loads environment variables from `.env` file
  - Used for Odoo credentials and configuration
  
- **xmlrpc.client** (Standard library)
  - XML-RPC client for Odoo API communication
  - Built-in to Python, no installation needed

### Frontend (React)
- **react** (18.3.1) - UI library
  - Core React library for building user interfaces
  - Uses functional components with hooks
  
- **react-dom** (18.3.1) - React DOM renderer
  - Renders React components to the DOM
  
- **react-i18next** (15.1.3) - Internationalization
  - React bindings for i18next
  - Provides `useTranslation` hook
  
- **i18next** (24.0.5) - i18n framework
  - Core internationalization framework
  - Handles language switching and translation loading

## Build Tools

### Frontend
- **vite** (5.4.10) - Build tool and dev server
  - Fast HMR (Hot Module Replacement)
  - Optimized production builds
  - Native ES modules support
  
- **@vitejs/plugin-react** (4.3.3) - React plugin for Vite
  - Enables React Fast Refresh
  - JSX transformation

## Development Dependencies

### Frontend
- **eslint** (9.13.0) - JavaScript linter
  - Code quality and style checking
  - Configured in `eslint.config.js`
  
- **eslint-plugin-react** (7.37.2) - React-specific linting rules
  - React best practices enforcement
  
- **eslint-plugin-react-hooks** (5.0.0) - React Hooks linting
  - Enforces Rules of Hooks
  
- **eslint-plugin-react-refresh** (0.4.14) - React Fast Refresh linting
  - Ensures components are Fast Refresh compatible
  
- **globals** (15.11.0) - Global variables definitions
  - Provides browser and Node.js globals for ESLint

## External Services

### Odoo (AwesomeFoodCoops)
- **Version**: 12.0 (likely, based on repository)
- **Protocol**: XML-RPC
- **Authentication**: Username/password
- **Modules Used**:
  - `coop_membership` - Member management, shares, family members
  - `coop_shift` - Shift scheduling, attendance, counter system
  
**Key Models:**
- `res.partner` - Members and contacts
- `pos.order` - Point of sale orders (purchases)
- `shift.registration` - Shift attendance records
- `shift.shift` - Shift instances
- `shift.counter.event` - Counter credit/debit events
- `shift.leave` - Member leave periods
- `shift.leave.type` - Leave type definitions

## Data Files

### Static Data
- **cycles_2025.json** - Shift cycle calendar
  - Defines 4-week cycles with weeks A, B, C, D
  - Used for timeline grouping
  - Independent of Odoo data
  - Format:
    ```json
    {
      "cycles": [
        {
          "cycle_number": 1,
          "start_date": "2025-01-06",
          "end_date": "2025-02-02",
          "weeks": [
            {
              "week_letter": "A",
              "start_date": "2025-01-06",
              "end_date": "2025-01-12"
            }
          ]
        }
      ]
    }
    ```

## Why These Choices

### Flask (Backend)
- **Lightweight**: Simple REST API doesn't need heavy framework
- **Python ecosystem**: Easy integration with XML-RPC client
- **Fast development**: Minimal boilerplate for API endpoints

### React + Vite (Frontend)
- **React**: Component-based architecture fits timeline UI well
- **Vite**: Much faster than Create React App, better DX
- **Hooks**: Modern React patterns, no class components needed

### react-i18next
- **Comprehensive**: Full-featured i18n solution
- **React integration**: Hooks-based API fits modern React
- **Language switching**: Built-in support for dynamic language changes
- **Interpolation**: Easy to inject dynamic values into translations

### Tailwind CSS (via CDN/utility classes)
- **Rapid development**: Utility-first approach speeds up styling
- **Consistency**: Design system built into class names
- **Responsive**: Mobile-first responsive utilities
- **Gradients**: Easy purple-pink gradient theme

### XML-RPC (Odoo)
- **Odoo standard**: Official Odoo external API protocol
- **Simple**: No complex authentication flows
- **Python support**: Built-in `xmlrpc.client` module

## Version Compatibility

### Python
- **Minimum**: Python 3.7+ (for type hints, f-strings)
- **Tested**: Python 3.9+

### Node.js
- **Minimum**: Node 18+ (for Vite 5)
- **Tested**: Node 20+

### Browser Support
- **Modern browsers**: Chrome, Firefox, Safari, Edge (latest 2 versions)
- **ES modules**: Required for Vite dev server
- **Intl API**: Required for date formatting

## Security Considerations

### Backend
- **CORS**: Configured to allow frontend origin
- **Environment variables**: Credentials stored in `.env`, not committed
- **Error handling**: Sensitive data not exposed in error messages

### Frontend
- **API URL**: Configurable via environment variable
- **No credentials**: Frontend doesn't store Odoo credentials
- **HTTPS**: Should be used in production

## Future Dependencies (Potential)

### Backend
- **pytest** - For unit testing
- **requests** - Alternative to xmlrpc.client if REST API needed
- **redis** - For caching Odoo responses

### Frontend
- **@testing-library/react** - For component testing
- **vitest** - For unit testing (Vite-compatible)
- **react-router-dom** - If multi-page navigation needed
