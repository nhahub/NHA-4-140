import csv
import psycopg2
from psycopg2.extras import execute_values
import os


def get_connection_string():
    env_path = os.path.join(os.path.dirname(__file__), 'Backend', 'supabase', '.env')
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('CONNECTION_STRING='):
                return line.split('=')[1].strip()
    raise ValueError("Connection string not found in .env")


def transfer_csv_to_supabase():
    connection_string = get_connection_string()
    
    # CSV file path
    csv_file_path = r'E:\DEPI-GENERATIVE-FINAL-PROJECT\Backend\final_data.csv'
    
    try:
        # Connect to the database
        print("Connecting to Supabase database...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f"Connected to PostgreSQL: {version[0]}")
        
        # Read the CSV file to understand its structure
        print("Reading CSV file...")
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Get the header row
            
            # Clean headers - remove any empty strings and strip whitespace
            headers = [h.strip() for h in headers if h.strip()]
            
            print(f"Found {len(headers)} columns: {headers}")
            
            # Create table if it doesn't exist
            table_name = "car_listings"  # You can change this name
            
            # Drop table if exists (for clean slate) - COMMENT THIS OUT IF YOU WANT TO KEEP EXISTING DATA
            # cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            # Create table with appropriate column types
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
            """
            
            # Add columns based on headers
            # We'll use TEXT for most columns for simplicity, but you might want to adjust based on data
            for header in headers:
                # Handle special characters in column names by replacing spaces and special chars
                clean_header = header.replace(' ', '_').replace('-', '_').replace('/', '_').replace('.', '_')
                create_table_query += f'    "{clean_header}" TEXT,\n'
            
            # Remove the trailing comma and close the table definition
            create_table_query = create_table_query.rstrip(',\n') + '\n);'
            
            print("Creating table...")
            cursor.execute(create_table_query)
            conn.commit()
            
            # Now insert the data
            print("Inserting data from CSV...")
            
            # Go back to the beginning of the file (after header)
            f.seek(0)
            next(reader)  # Skip header again
            
            # Prepare data for insertion
            rows = []
            for row in reader:
                # Clean the row data - take only the number of elements that match headers
                cleaned_row = [cell.strip() if cell.strip() else None for cell in row[:len(headers)]]
                # If row has fewer elements than headers, pad with None
                while len(cleaned_row) < len(headers):
                    cleaned_row.append(None)
                rows.append(tuple(cleaned_row))
            
            # Insert data using execute_values for better performance
            if rows:
                columns = ', '.join([f'"{h.replace(" ", "_").replace("-", "_").replace("/", "_").replace(".", "_")}"' for h in headers])
                insert_query = f"""
                INSERT INTO {table_name} ({columns}) 
                VALUES %s
                """
                
                execute_values(cursor, insert_query, rows)
                conn.commit()
                print(f"Successfully inserted {len(rows)} rows into {table_name}")
            else:
                print("No data rows found in CSV")
                
        # Close connections
        cursor.close()
        conn.close()
        print("Transfer completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    transfer_csv_to_supabase()