import os
import json
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

def get_db_connection():
    conn_str = os.environ.get('DATABASE_URL')
    if not conn_str:
        env_path = os.path.join(os.path.dirname(__file__), '..', 'Backend', 'supabase', '.env')
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('CONNECTION_STRING='):
                    conn_str = line.split('=')[1].strip()
                    break
    return psycopg2.connect(conn_str, cursor_factory=RealDictCursor)


@app.route('/api/cars', methods=['GET'])
def get_cars():
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM car_listings")
        total = cursor.fetchone()['count']

        cursor.execute("""
            SELECT * FROM car_listings 
            ORDER BY id 
            LIMIT %s OFFSET %s
        """, (limit, offset))
        cars = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            'cars': [dict(row) for row in cars],
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cars/<int:car_id>', methods=['GET'])
def get_car(car_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM car_listings WHERE id = %s", (car_id,))
        car = cursor.fetchone()

        cursor.close()
        conn.close()

        if car:
            return jsonify(dict(car))
        else:
            return jsonify({'error': 'Car not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cars/search', methods=['GET'])
def search_cars():
    try:
        brand = request.args.get('brand', '')
        model = request.args.get('model', '')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM car_listings WHERE 1=1"
        params = []

        if brand:
            query += " AND brand ILIKE %s"
            params.append(f'%{brand}%')
        if model:
            query += " AND model ILIKE %s"
            params.append(f'%{model}%')
        if min_price:
            query += " AND price::numeric >= %s"
            params.append(min_price)
        if max_price:
            query += " AND price::numeric <= %s"
            params.append(max_price)

        cursor.execute(f"SELECT COUNT(*) FROM ({query}) as subquery", params)
        total = cursor.fetchone()['count']

        query += " ORDER BY id LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        cars = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            'cars': [dict(row) for row in cars],
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit if total > 0 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cars/brands', methods=['GET'])
def get_brands():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT brand FROM car_listings ORDER BY brand")
        brands = [row['brand'] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({'brands': brands})
    except Exception as e:
        return jsonify({'error': str(e)}), 500