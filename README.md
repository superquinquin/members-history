# Members History - Superquinquin

A web application to display member history for the Superquinquin cooperative supermarket, showing purchases, shift participation, and attendance records.

## Project Structure

```
members-history/
├── backend/          # Flask API server
│   ├── app.py       # Main Flask application
│   ├── odoo_client.py  # Odoo API client
│   ├── requirements.txt
│   └── .env.example
└── frontend/         # React application
    ├── src/
    ├── package.json
    └── .env.example
```

## Backend Setup

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your Odoo instance details:
- `ODOO_URL`: Your Odoo instance URL
- `ODOO_DB`: Database name
- `ODOO_USERNAME`: Odoo username
- `ODOO_PASSWORD`: Odoo password

5. Run the server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Frontend Setup

### Prerequisites
- Node.js 18+
- npm

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
```bash
cp .env.example .env
```

4. Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## API Endpoints

- `GET /api/health` - Health check endpoint
- `GET /api/member/<member_id>/history` - Get member history

## Tech Stack

**Backend:**
- Flask - Web framework
- Flask-CORS - CORS support
- python-dotenv - Environment variable management
- xmlrpc - Odoo API communication

**Frontend:**
- React - UI framework
- Vite - Build tool
- Tailwind CSS - Styling

## Development

The application uses:
- Flask development server with hot reload
- Vite dev server with HMR (Hot Module Replacement)

## Odoo API

The application connects to Odoo using XML-RPC. See the [Odoo API documentation](https://www.odoo.com/documentation/13.0/developer/api/odoo.html) for more details.
