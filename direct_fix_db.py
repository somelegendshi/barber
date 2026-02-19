import psycopg2
import os
from dotenv import load_dotenv

# Absolute path to your project's .env
env_path = r"C:\Users\Legion\Documents\barber_booking_bot\.env"
load_dotenv(dotenv_path=env_path)

db_url = os.getenv("DATABASE_URL")

def fix_sequences_raw():
    tables = ['shops', 'barbers', 'services', 'bookings', 'customers', 'work_hours', 'time_off']
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    print(f"Connecting to: {db_url}")
    
    for table in tables:
        print(f"Fixing sequence for: {table}...")
        # This fixes the sequence to match the actual Max ID in the table
        sql = f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1), true);"
        cur.execute(sql)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database sequences fixed directly via Psycopg2.")

if __name__ == "__main__":
    try:
        fix_sequences_raw()
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
