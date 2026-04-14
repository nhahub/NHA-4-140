import psycopg2

def test_connection():
    # Database connection parameters for Supabase local
    db_params = {
        'host': 'localhost',
        'port': 54322,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'postgres'  # Default password for Supabase local
    }
    
    try:
        # Connect to the database
        print("Connecting to Supabase database...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f"Connected to PostgreSQL: {version[0]}")
        
        # List tables
        cursor.execute("""SELECT table_name FROM information_schema.tables 
                          WHERE table_schema = 'public' ORDER BY table_name;""")
        tables = cursor.fetchall()
        print('Tables in database:')
        for table in tables:
            print(f'  - {table[0]}')
            
        # Close connections
        cursor.close()
        conn.close()
        print("Connection test completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_connection()