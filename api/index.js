const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
app.use(cors());
app.use(express.json());

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

app.get('/api/cars', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;

    const countResult = await pool.query('SELECT COUNT(*) FROM car_listings');
    const total = parseInt(countResult.rows[0].count);

    const carsResult = await pool.query(
      'SELECT * FROM car_listings ORDER BY id LIMIT $1 OFFSET $2',
      [limit, offset]
    );

    res.json({
      cars: carsResult.rows,
      total,
      page,
      limit,
      total_pages: Math.ceil(total / limit),
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/cars/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query('SELECT * FROM car_listings WHERE id = $1', [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Car not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/cars/search', async (req, res) => {
  try {
    const { brand, model, min_price, max_price } = req.query;
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;

    let query = 'SELECT * FROM car_listings WHERE 1=1';
    const params = [];
    let paramIndex = 1;

    if (brand) {
      query += ` AND brand ILIKE $${paramIndex}`;
      params.push(`%${brand}%`);
      paramIndex++;
    }
    if (model) {
      query += ` AND model ILIKE $${paramIndex}`;
      params.push(`%${model}%`);
      paramIndex++;
    }
    if (min_price) {
      query += ` AND price::numeric >= $${paramIndex}`;
      params.push(parseFloat(min_price));
      paramIndex++;
    }
    if (max_price) {
      query += ` AND price::numeric <= $${paramIndex}`;
      params.push(parseFloat(max_price));
      paramIndex++;
    }

    const countResult = await pool.query(`SELECT COUNT(*) FROM (${query}) as subquery`, params);
    const total = parseInt(countResult.rows[0].count);

    query += ` ORDER BY id LIMIT $${paramIndex} OFFSET ${paramIndex + 1}`;
    params.push(limit, offset);

    const carsResult = await pool.query(query, params);

    res.json({
      cars: carsResult.rows,
      total,
      page,
      limit,
      total_pages: Math.ceil(total / limit),
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/cars/brands', async (req, res) => {
  try {
    const result = await pool.query('SELECT DISTINCT brand FROM car_listings ORDER BY brand');
    res.json({ brands: result.rows.map((row) => row.brand) });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = app;