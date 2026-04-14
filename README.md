# AI Car Marketplace - Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Backend Documentation](./docs/backend.md)
4. [Frontend Documentation](./docs/frontend.md)
5. [Database Setup](./docs/database.md)
6. [API Documentation](./docs/api.md)
7. [Installation Guide](./docs/installation.md)
8. [Troubleshooting](./docs/troubleshooting.md)

---

## Project Overview

This is an AI-powered car marketplace monorepo that connects a React frontend with a Supabase PostgreSQL database via a Flask backend API.

### Key Features
- AI-powered car recommendations
- Real-time car listings from Supabase database
- Search and filter functionality
- Responsive dark/light theme
- Modern UI with Tailwind CSS

### Tech Stack
- **Frontend**: React 18, Vite, Tailwind CSS, React Router
- **Backend**: Flask, psycopg2
- **Database**: PostgreSQL (Supabase)
- **Testing**: pytest

---

## Project Structure

```
DEPI-GENERATIVE-FINAL-PROJECT/
├── Backend/                    # Flask backend API
│   ├── app.py                 # Main Flask application
│   ├── ingest_data.py         # Data ingestion script
│   ├── test_supabase.py       # Database tests
│   ├── supabase/              # Supabase configuration
│   │   └── .env               # Environment variables
│   └── final_data.csv         # Car listings data
│
├── FRONT-END/                 # React frontend
│   ├── src/
│   │   ├── api/               # API client
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── context/           # React contexts
│   │   ├── hooks/             # Custom hooks
│   │   └── data/              # Mock data
│   ├── package.json
│   └── vite.config.js
│
├── docs/                      # Documentation
│   ├── backend.md
│   ├── frontend.md
│   ├── database.md
│   ├── api.md
│   ├── installation.md
│   └── troubleshooting.md
│
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Supabase account

### Installation

1. **Clone and install dependencies:**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt

   # Install frontend dependencies
   cd FRONT-END
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   # Backend - Create Backend/supabase/.env
   CONNECTION_STRING=postgresql://postgres:YOUR_PASSWORD@db.YOUR_REF.supabase.co:5432/postgres
   ```

3. **Run the application:**
   ```bash
   # Terminal 1: Start backend
   python Backend/app.py

   # Terminal 2: Start frontend
   cd FRONT-END
   npm run dev
   ```

4. **Access the app:** http://localhost:5173

---

## Available Scripts

### Backend
- `python Backend/app.py` - Start Flask API server
- `python Backend/ingest_data.py` - Ingest 500 rows to database
- `python -m pytest Backend/test_supabase.py` - Run tests

### Frontend
- `cd FRONT-END && npm run dev` - Start dev server
- `cd FRONT-END && npm run build` - Build for production
- `cd FRONT-END && npm run lint` - Run ESLint

---

## License

MIT License