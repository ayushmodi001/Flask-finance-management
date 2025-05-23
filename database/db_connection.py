import psycopg2
from psycopg2 import OperationalError
from config import DB_HOST, DB_NAME, DB_USER, DB_PASS
import time

def create_db_connection(max_retries=3, retry_delay=2):
    """Ensure the database exists and establish a connection with retry mechanism."""
    retries = 0
    last_error = None
    
    while retries < max_retries:
        try:
            # Connect to the default PostgreSQL database to check for DB existence
            print(f"Attempting to connect to PostgreSQL (attempt {retries + 1}/{max_retries})...")
            temp_conn = psycopg2.connect(
                host=DB_HOST,
                dbname="postgres",  # Default DB to perform admin operations
                user=DB_USER,
                password=DB_PASS
            )
            temp_conn.autocommit = True
            cur = temp_conn.cursor()

            # Check if the database exists
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
            exists = cur.fetchone()

            # If the database does not exist, create it
            if not exists:
                print(f"Database '{DB_NAME}' does not exist. Creating it now...")
                cur.execute(f"CREATE DATABASE {DB_NAME}")
                print(f"Database '{DB_NAME}' created successfully.")

            cur.close()
            temp_conn.close()

            # Now connect to the actual application database
            conn = psycopg2.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            print("Database connection established successfully.")
            return conn

        except OperationalError as e:
            last_error = e
            retries += 1
            if retries < max_retries:
                print(f"Database connection error: {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts: {e}")
        except Exception as e:
            print(f"Unexpected database error: {e}")
            last_error = e
            break
    
    print(f"Database connection failed: {last_error}")
    return None
