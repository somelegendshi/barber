from app.db.conn import get_db
import os
from dotenv import load_dotenv

# Force load the .env file with the absolute path
env_path = r"C:\Users\Legion\Documents\barber_booking_bot\.env"
load_dotenv(dotenv_path=env_path)

# Set the environment variable manually if load_dotenv is being stubborn
os.environ["DATABASE_URL"] = "postgresql://postgres:2531365@localhost:5432/barber_bot_db"

def fix_sequences():
    tables = ['shops', 'barbers', 'services', 'bookings', 'customers', 'work_hours', 'time_off']
    
    with get_db() as cur:
        for table in tables:
            print(f"Fixing sequence for table: {table}...")
            # Setval to the current MAX(id). 
            # If the table is empty, COALESCE to 1 so the next insert is 1.
            sql = f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1), true);"
            cur.execute(sql)
        print("✅ All sequences synchronized with existing data.")

if __name__ == "__main__":
    try:
        fix_sequences()
    except Exception as e:
        print(f"❌ Error: {e}")
