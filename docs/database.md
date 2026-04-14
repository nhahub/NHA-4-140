# Database Documentation

## Overview
The database is hosted on Supabase (PostgreSQL 17) and stores all car listings data.

## Connection Details

### From `Backend/supabase/.env`
```
CONNECTION_STRING=postgresql://postgres:DEPIFINALPROJECT@db.icjteilmbreuuukimxho.supabase.co:5432/postgres
```

**Connection Info:**
- **Host**: db.icjteilmbreuuukimxho.supabase.co
- **Port**: 5432
- **Database**: postgres
- **User**: postgres
- **Password**: DEPIFINALPROJECT

## Database Schema

### Table: `car_listings`

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| brand | TEXT | Car brand (e.g., "Toyota") |
| model | TEXT | Car model (e.g., "Camry") |
| year | TEXT | Manufacturing year |
| price | TEXT | Price in EGP (e.g., "450,000 EGP") |
| condition | TEXT | Car condition (e.g., "Used", "New") |
| color | TEXT | Car color |
| transmission | TEXT | Transmission type ("Manual", "Automatic") |
| km | TEXT | Kilometers driven |
| fuel_type | TEXT | Fuel type ("Gas", "Diesel", "Electric") |
| posted_on | TEXT | Date posted |
| last_updated | TEXT | Last update date |
| location | TEXT | Car location |
| description | TEXT | Full description |
| url | TEXT | Source URL |

## Current Data

- **Total Rows**: 7,664+
- **Data Source**: `Backend/final_data.csv`
- **Columns**: 14

## Sample Query

```sql
-- Get all cars with pagination
SELECT * FROM car_listings 
ORDER BY id 
LIMIT 20 OFFSET 0;

-- Get cars by brand
SELECT * FROM car_listings 
WHERE brand = 'Toyota';

-- Get unique brands
SELECT DISTINCT brand FROM car_listings ORDER BY brand;

-- Get total count
SELECT COUNT(*) FROM car_listings;
```

## Managing Database

### Connect via psql
```bash
psql postgresql://postgres:DEPIFINALPROJECT@db.icjteilmbreuuukimxho.supabase.co:5432/postgres
```

### Connect via Python
```python
import psycopg2

conn = psycopg2.connect(
    "postgresql://postgres:DEPIFINALPROJECT@db.icjteilmbreuuukimxho.supabase.co:5432/postgres"
)
```

## Data Ingestion

### From CSV to Database

1. **Run the transfer script** (creates table + inserts all data):
   ```bash
   python transfer_to_supabase.py
   ```

2. **Ingest specific number of rows**:
   ```bash
   python Backend/ingest_data.py  # 500 rows by default
   ```

   Or modify the number:
   ```python
   from Backend.ingest_data import ingest_data
   ingest_data(1000)  # Ingest 1000 rows
   ```

### CSV Format
The CSV should have headers matching database columns:
```csv
brand,model,year,price,condition,color,transmission,km,fuel_type,posted_on,last_updated,location,description,url
```

## Supabase Console

To manage the database via Supabase:
1. Go to https://supabase.com/dashboard
2. Select your project
3. Navigate to **SQL Editor** for queries
4. Navigate to **Table Editor** for visual data management

## Security Notes

- The `.env` file contains credentials - do not commit to version control
- Supabase provides row-level security (RLS) - configure as needed
- Consider enabling RLS on `car_listings` table for production

## Troubleshooting

### Connection Refused
- Check if Supabase project is not paused
- Verify network connectivity
- Check firewall settings

### Data Not Appearing
- Verify data was ingested:
  ```sql
  SELECT COUNT(*) FROM car_listings;
  ```
- Check table exists:
  ```sql
  SELECT table_name FROM information_schema.tables 
  WHERE table_schema = 'public';
  ```