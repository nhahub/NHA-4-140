# Cars Marketplace Backend

FastAPI backend for the Cars Marketplace platform. Provides REST APIs for
authentication, car listings, search (vector + full-text), favorites,
comparisons, and an AI chat assistant.

## Tech Stack

- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL via asyncpg, Supabase (auth + storage)
- **Vector Search:** Qdrant + fastembed (all-MiniLM-L6-v2)
- **AI:** Google Gemini, Tavily search API
- **Auth:** JWT (python-jose) + bcrypt

## Project Structure

```
Backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Pydantic settings (reads .env)
│   ├── dependencies.py      # FastAPI dependency injection
│   ├── core/
│   │   ├── exceptions.py    # Custom exception classes
│   │   ├── middleware.py    # CORS middleware
│   │   └── security.py      # JWT / password helpers
│   ├── db/
│   │   ├── client.py        # DB, Supabase, Qdrant client factories
│   │   └── queries/         # SQL query helpers
│   ├── routers/             # API route handlers
│   │   ├── auth.py          # Signup / login / refresh
│   │   ├── users.py         # Profile CRUD + avatar upload
│   │   ├── ads.py           # Car ad CRUD + images
│   │   ├── search.py        # Full-text + vector search
│   │   ├── favorites.py     # User favorites
│   │   ├── chat.py          # AI chat assistant
│   │   └── compare.py       # Side-by-side car comparison
│   ├── schemas/             # Pydantic request/response models
│   └── services/            # Business logic layer
├── .env.example             # Environment variable template
├── Dockerfile               # Production container
└── requirements.txt         # Python dependencies
```

## Prerequisites

- Python 3.11+
- PostgreSQL (or Supabase project)
- Qdrant instance (cloud or local)
- Gemini API key
- Tavily API key

## Setup

**1. Clone the repo and navigate to the backend directory:**

```bash
cd Backend
```

**2. Create a virtual environment and install dependencies:**

```bash
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

**3. Configure environment variables:**

```bash
cp .env.example .env
```

Edit `.env` with your credentials (see `.env.example` for all required fields).

**4. Start the development server:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

## Docker

```bash
docker build -t cars-backend .
docker run -p 8000:8000 --env-file .env cars-backend
```

## API Endpoints

All routes are prefixed with `/api/v1`.

| Group       | Endpoints                                      |
|-------------|------------------------------------------------|
| Auth        | `POST /auth/signup`, `POST /auth/login`, `POST /auth/refresh` |
| Users       | `GET/PUT /users/me`, `POST /users/me/avatar`   |
| Ads         | `GET/POST /ads`, `GET/PUT/DELETE /ads/{id}`, `POST /ads/{id}/images` |
| Search      | `GET /search?q=...`                            |
| Favorites   | `GET/POST /favorites`, `DELETE /favorites/{id}` |
| Chat        | `POST /chat` (AI assistant)                    |
| Compare     | `POST /compare`                                |
| Health      | `GET /health`                                  |
