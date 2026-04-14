import csv
import psycopg2
from psycopg2.extras import execute_values
import os


def get_connection_string():
    env_path = os.path.join(os.path.dirname(__file__), 'supabase', '.env')
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('CONNECTION_STRING='):
                return line.split('=')[1].strip()
    raise ValueError("Connection string not found in .env")


def ingest_data(limit=500):
    connection_string = get_connection_string()
    csv_file_path = r'E:\DEPI-GENERATIVE-FINAL-PROJECT\Backend\final_data.csv'
    table_name = "car_listings"

    try:
        print("Connecting to Supabase database...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        print(f"Reading first {limit} rows from CSV...")
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            headers = [h.strip() for h in headers if h.strip()]

            rows = []
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                cleaned_row = [cell.strip() if cell.strip() else None for cell in row[:len(headers)]]
                while len(cleaned_row) < len(headers):
                    cleaned_row.append(None)
                rows.append(tuple(cleaned_row))

        print(f"Inserting {len(rows)} rows into {table_name}...")
        columns = ', '.join([f'"{h.replace(" ", "_").replace("-", "_").replace("/", "_").replace(".", "_")}"' for h in headers])
        insert_query = f"""
        INSERT INTO {table_name} ({columns}) 
        VALUES %s
        """

        execute_values(cursor, insert_query, rows)
        conn.commit()
        print(f"Successfully inserted {len(rows)} rows")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()


if __name__ == "__main__":
    ingest_data(500)