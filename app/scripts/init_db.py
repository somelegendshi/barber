import os
import sys
from dotenv import load_dotenv

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../.."))
load_dotenv()

from app.db.conn import get_db

def initialize_production_db():
    print("🚀 Running Database Migrations...")
    
    try:
        with get_db() as cur:
            # 1. Ensure 'username' exists in 'customers'
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='customers' AND column_name='username';
            """)
            if not cur.fetchone():
                print("➕ Adding 'username' column to 'customers'...")
                cur.execute("ALTER TABLE customers ADD COLUMN username TEXT;")

            # 2. Ensure 'telegram_id' exists in 'barbers'
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='barbers' AND column_name='telegram_id';
            """)
            if not cur.fetchone():
                print("➕ Adding 'telegram_id' column to 'barbers'...")
                cur.execute("ALTER TABLE barbers ADD COLUMN telegram_id BIGINT;")

            # 3. Create other tables if they don't exist (using schema.sql)
            schema_path = os.path.join(current_dir, "../db/schema.sql")
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            cur.execute(schema_sql)
            
            print("✅ Database is up to date.")
                
    except Exception as e:
        print(f"❌ Migration Failed: {e}")

if __name__ == "__main__":
    initialize_production_db()
