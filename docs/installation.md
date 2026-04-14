# Installation Guide

## Prerequisites

Ensure you have the following installed:

| Tool | Version | Notes |
|------|---------|-------|
| Node.js | 18+ | For frontend |
| Python | 3.10+ | For backend |
| pip | Latest | Package manager for Python |
| npm | 10+ | Comes with Node.js |

## Step 1: Clone the Project

```bash
git clone <repository-url>
cd DEPI-GENERATIVE-FINAL-PROJECT
```

## Step 2: Install Backend Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

**Required packages:**
- psycopg2-binary - PostgreSQL adapter
- python-dotenv - Environment variables
- flask - Web framework
- flask-cors - CORS support
- pytest - Testing

## Step 3: Configure Environment Variables

Create or verify the Supabase connection in:
```
Backend/supabase/.env
```

Contents:
```env
CONNECTION_STRING=postgresql://postgres:YOUR_PASSWORD@db.YOUR_REF.supabase.co:5432/postgres
```

## Step 4: Install Frontend Dependencies

```bash
cd FRONT-END
npm install
```

## Step 5: Verify Database Setup

Test the database connection:
```bash
python -m pytest Backend/test_supabase.py -v
```

Expected output:
```
Backend/test_supabase.py::test_supabase_connection PASSED
Backend/test_supabase.py::test_supabase_tables_exist PASSED
Backend/test_supabase.py::test_car_listings_table PASSED
```

If tests fail, check:
1. Supabase project is running (not paused)
2. Network connectivity to Supabase
3. Connection string is correct in `.env`

## Step 6: Ingest Data (First Time)

If database is empty, populate with data:

```bash
# Transfer all data from CSV
python transfer_to_supabase.py

# Or ingest specific number of rows
python Backend/ingest_data.py
```

## Step 7: Start the Backend

```bash
# Terminal 1
python Backend/app.py
```

Should see:
```
* Serving Flask app 'app'
* Debug mode: on
* Running on http://127.0.0.1:5000
```

## Step 8: Start the Frontend

```bash
# Terminal 2
cd FRONT-END
npm run dev
```

Should see:
```
  VITE v6.4.1  ready in 300 ms
  ➜  Local:   http://localhost:5173/
```

## Step 9: Access the Application

Open browser to: **http://localhost:5173**

You should see the car marketplace with real data from Supabase.

## Quick Start Script

For convenience, you can run both servers with one command using a shell script:

**Windows (PowerShell) - run-servers.ps1**
```powershell
Start-Process python -ArgumentList "Backend\app.py"
Start-Process npm -WorkingDirectory "FRONT-END" -ArgumentList "run dev"
```

## Development Workflow

1. Start backend first (port 5000)
2. Start frontend (port 5173)
3. Make changes in either folder
4. Frontend hot-reloads on changes
5. Backend auto-reloads with Flask debug mode

## Production Build

### Frontend
```bash
cd FRONT-END
npm run build
# Output in FRONT-END/dist/
```

### Backend
Use a production WSGI server (Gunicorn):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Uninstall

```bash
# Remove node_modules
cd FRONT-END && rm -rf node_modules

# Remove virtual environment (if created)
cd ..
rmdir /s .venv
```