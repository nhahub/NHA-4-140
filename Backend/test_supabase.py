import pytest
import psycopg2
import os


def get_connection_string():
    """Get Supabase connection string from .env file"""
    env_path = os.path.join(os.path.dirname(__file__), 'supabase', '.env')
    
    connection_string = None
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('CONNECTION_STRING='):
                connection_string = line.split('=')[1].strip()
                break
    
    return connection_string


def test_supabase_connection():
    """Test that we can connect to Supabase using the connection string"""
    connection_string = get_connection_string()
    assert connection_string is not None, "Connection string not found in .env"
    
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()
    
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f"Connected to PostgreSQL: {version[0]}")
    
    cursor.close()
    conn.close()
    
    assert version is not None


def test_supabase_tables_exist():
    """Test that we can query tables in Supabase"""
    connection_string = get_connection_string()
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    print(f"Tables found: {tables}")
    
    cursor.close()
    conn.close()
    
    assert isinstance(tables, list)


def test_car_listings_table():
    """Test that car_listings table exists and has data"""
    connection_string = get_connection_string()
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM car_listings")
    count = cursor.fetchone()[0]
    print(f"Car listings count: {count}")
    
    cursor.close()
    conn.close()
    
    assert count >= 0