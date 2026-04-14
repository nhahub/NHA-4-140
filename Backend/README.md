# Backend Documentation

## Overview
The backend is a Flask REST API that connects to Supabase PostgreSQL database and serves car listings to the frontend.

## Technology Stack
- **Framework**: Flask 3.0+
- **Database**: PostgreSQL (via psycopg2)
- **CORS**: Flask-CORS

## Project Structure

```
Backend/
├── app.py                 # Main Flask application (API endpoints)
├── ingest_data.py         # Script to ingest CSV data to database
├── test_supabase.py       # pytest tests for database connection
├── supabase/
│   └── .env               # Supabase connection string
├── final_data.csv         # Original car data
└── README.md              # This file
```

## API Endpoints

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### 1. Get All Cars
```
GET /api/cars?page=1&limit=20
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| limit | int | 20 | Items per page |

**Response:**
```json
{
  "cars": [
    {
      "id": 1,
      "brand": "Toyota",
      "model": "Camry",
      "year": 2023,
      "price": "450,000 EGP",
      ...
    }
  ],
  "total": 7664,
  "page": 1,
  "limit": 20,
  "total_pages": 384
}
```

#### 2. Get Single Car
```
GET /api/cars/<id>
```

**Response:**
```json
{
  "id": 1,
  "brand": "Toyota",
  "model": "Camry",
  ...
}
```

#### 3. Search Cars
```
GET /api/cars/search?brand=Toyota&min_price=100000&max_price=500000
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| brand | string | Filter by brand (case-insensitive) |
| model | string | Filter by model |
| min_price | float | Minimum price |
| max_price | float | Maximum price |
| page | int | Page number |
| limit | int | Items per page |

#### 4. Get All Brands
```
GET /api/cars/brands
```

**Response:**
```json
{
  "brands": ["Toyota", "BMW", "Mercedes", ...]
}
```

## Running the Backend

### Development
```bash
python Backend/app.py
```

The server will start on `http://localhost:5000`

### Configuration

The database connection is configured via `Backend/supabase/.env`:
```
CONNECTION_STRING=postgresql://postgres:PASSWORD@db.REF.supabase.co:5432/postgres
```

## Testing

```bash
python -m pytest Backend/test_supabase.py -v
```

Tests:
- `test_supabase_connection` - Verifies database connection
- `test_supabase_tables_exist` - Checks tables in public schema
- `test_car_listings_table` - Verifies car_listings table exists with data

## Data Ingestion

To ingest 500 rows from CSV to database:
```bash
python Backend/ingest_data.py
```

To ingest custom amount:
```python
from ingest_data import ingest_data
ingest_data(1000)  # Ingest 1000 rows
```

## Error Handling

All endpoints return JSON responses. Errors include:
```json
{
  "error": "Error message"
}
```

Common status codes:
- 200: Success
- 404: Not found
- 500: Server error