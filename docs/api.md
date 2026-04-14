# API Documentation

## Base URL
```
http://localhost:5000/api
```

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cars` | Get all cars with pagination |
| GET | `/cars/<id>` | Get single car by ID |
| GET | `/cars/search` | Search/filter cars |
| GET | `/cars/brands` | Get all unique brands |

---

## GET /api/cars

Get paginated list of car listings.

### URL
```
GET http://localhost:5000/api/cars?page=1&limit=20
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number (1-indexed) |
| limit | integer | No | 20 | Number of items per page (max 100) |

### Example Request
```javascript
fetch('http://localhost:5000/api/cars?page=1&limit=12')
```

### Success Response (200)
```json
{
  "cars": [
    {
      "id": 1,
      "brand": "Mitsubishi",
      "model": "Global News",
      "year": "1998.0",
      "price": "250,000 EGP",
      "condition": "Used",
      "color": "Blue",
      "transmission": "Manual",
      "km": "999,999 KM",
      "fuel_type": "Gas",
      "posted_on": "2026-01-28",
      "last_updated": "2026-01-28",
      "location": "Suez",
      "description": "The car is completely factory-made...",
      "url": "https://eg.hatla2ee.com/..."
    }
  ],
  "total": 7664,
  "page": 1,
  "limit": 20,
  "total_pages": 384
}
```

### Error Response (500)
```json
{
  "error": "Connection string not found in .env"
}
```

---

## GET /api/cars/<id>

Get a single car by its ID.

### URL
```
GET http://localhost:5000/api/cars/1
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Car ID |

### Success Response (200)
```json
{
  "id": 1,
  "brand": "Mitsubishi",
  "model": "Global News",
  "year": "1998.0",
  "price": "250,000 EGP",
  "condition": "Used",
  "color": "Blue",
  "transmission": "Manual",
  "km": "999,999 KM",
  "fuel_type": "Gas",
  "posted_on": "2026-01-28",
  "last_updated": "2026-01-28",
  "location": "Suez",
  "description": "The car is completely factory-made...",
  "url": "https://eg.hatla2ee.com/..."
}
```

### Error Response (404)
```json
{
  "error": "Car not found"
}
```

---

## GET /api/cars/search

Search and filter cars with multiple criteria.

### URL
```
GET http://localhost:5000/api/cars/search?brand=Toyota&min_price=100000&max_price=500000&page=1&limit=20
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| brand | string | No | Filter by brand (case-insensitive, partial match) |
| model | string | No | Filter by model (case-insensitive, partial match) |
| min_price | float | No | Minimum price (numeric value) |
| max_price | float | No | Maximum price (numeric value) |
| page | integer | No | Page number (default: 1) |
| limit | integer | No | Items per page (default: 20) |

### Example Request
```javascript
// Search for Toyota cars between 100k and 500k
fetch('http://localhost:5000/api/cars/search?brand=Toyota&min_price=100000&max_price=500000')
```

### Success Response (200)
```json
{
  "cars": [
    {
      "id": 100,
      "brand": "Toyota",
      "model": "Camry",
      "price": "450,000 EGP",
      ...
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 20,
  "total_pages": 2
}
```

### Notes on Price Filtering
- The price column stores values as text with "EGP" (e.g., "450,000 EGP")
- The API converts to numeric for comparison
- Prices with commas are handled correctly

---

## GET /api/cars/brands

Get list of all unique car brands in the database.

### URL
```
GET http://localhost:5000/api/cars/brands
```

### Success Response (200)
```json
{
  "brands": [
    "BMW",
    "Mercedes",
    "Toyota",
    "Hyundai",
    "Kia",
    "Audi",
    "Tesla",
    "Mitsubishi",
    ...
  ]
}
```

---

## Error Handling

All errors return JSON with an `error` field:

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 404 | Not found |
| 500 | Server error |

Example error response:
```json
{
  "error": "Failed to connect to database"
}
```

---

## Testing with cURL

```bash
# Get all cars
curl http://localhost:5000/api/cars

# Get car with ID 1
curl http://localhost:5000/api/cars/1

# Search for Toyota
curl "http://localhost:5000/api/cars/search?brand=Toyota"

# Get all brands
curl http://localhost:5000/api/cars/brands
```

---

## Frontend Integration

The frontend uses `src/api/carApi.js` to make requests:

```javascript
import { fetchCars, fetchCar, searchCars, fetchBrands } from './api/carApi';

// Get cars
const data = await fetchCars(1, 12);

// Search
const results = await searchCars({ brand: 'Toyota', max_price: 500000 });

// Get brands
const { brands } = await fetchBrands();
```