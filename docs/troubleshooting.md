# Troubleshooting Guide

## Common Issues and Solutions

---

## Backend Issues

### Issue: `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
pip install flask flask-cors
```

---

### Issue: `could not translate host name "db.xxx.supabase.co" to address`

**Causes:**
1. No internet connection
2. DNS resolution blocked
3. Supabase project is paused

**Solutions:**
1. Check internet: `ping google.com`
2. Check Supabase dashboard - ensure project is not paused
3. Try using IPv6 address directly (from `nslookup`)

---

### Issue: `connection refused` on port 5000

**Solution:**
```bash
# Kill any process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or use a different port
# Edit Backend/app.py and change:
app.run(debug=True, port=5000)  # Change to 5001
```

---

### Issue: `Connection to server at "localhost" failed`

**Cause:** Script is trying to connect to local Supabase instead of cloud.

**Solution:** Ensure `transfer_to_supabase.py` uses the connection string from `.env`, not hardcoded localhost values.

---

## Database Issues

### Issue: `psycopg2.OperationalError: authentication failed`

**Solution:**
Check password in `Backend/supabase/.env`:
```
CONNECTION_STRING=postgresql://postgres:CORRECT_PASSWORD@...
```

---

### Issue: `relation "car_listings" does not exist`

**Solution:**
Create the table by running the data transfer:
```bash
python transfer_to_supabase.py
```

---

### Issue: Tests pass but no data in frontend

**Solution:**
1. Check row count in database:
```python
import psycopg2
conn = psycopg2.connect("CONNECTION_STRING")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM car_listings")
print(cur.fetchone())
```

2. Run ingest script:
```bash
python Backend/ingest_data.py
```

---

## Frontend Issues

### Issue: `Failed to fetch` in browser console

**Causes:**
1. Backend not running
2. CORS not configured
3. Wrong API URL

**Solutions:**
1. Start backend: `python Backend/app.py`
2. Check browser console for exact error
3. Verify `src/api/carApi.js` has correct base URL

---

### Issue: `net::ERR_CONNECTION_REFUSED`

**Solution:**
Backend not running. Start it:
```bash
python Backend/app.py
```

---

### Issue: CORS error in console

**Solution:**
Ensure Flask has CORS enabled. In `Backend/app.py`:
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
```

---

### Issue: Page loads but no cars displayed

**Solutions:**
1. Check Network tab in browser dev tools
2. Verify API response at http://localhost:5000/api/cars
3. Check console for JavaScript errors

---

### Issue: Build fails with `npm run build`

**Solution:**
```bash
cd FRONT-END
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## Network Issues

### Issue: `getaddrinfo failed` for Supabase

**Cause:** DNS cannot resolve Supabase hostname

**Solutions:**
1. Check if you can ping the host:
```bash
nslookup db.icjteilmbreuuukimxho.supabase.co
```
2. Use a different DNS server (8.8.8.8)
3. Check firewall/proxy settings

---

### Issue: Works on one machine but not another

**Cause:** Network restrictions or DNS differences

**Solutions:**
1. Use VPN if behind corporate firewall
2. Check Windows hosts file
3. Verify both machines can reach google.com

---

## Data Issues

### Issue: Price filtering doesn't work

**Cause:** Price is stored as text with "EGP" suffix

**Solution:** The backend handles this, but ensure you're passing numeric values:
```
?min_price=100000&max_price=500000
```

---

### Issue: Duplicate data in database

**Solution:** Clear and re-ingest:
```python
# In Supabase SQL Editor:
TRUNCATE TABLE car_listings;

# Then:
python transfer_to_supabase.py
```

---

## Getting Help

1. Check backend logs in terminal
2. Check browser console (F12)
3. Test API directly: http://localhost:5000/api/cars
4. Run tests: `python -m pytest Backend/test_supabase.py -v`
5. Check Supabase dashboard for database status