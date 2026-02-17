import os
import sys
from dotenv import load_dotenv

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../.."))
load_dotenv()

from app.db.conn import get_db

def initialize_production_db():
    print("🚀 Initializing Production Database...")
    
    schema_path = os.path.join(current_dir, "../db/schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    try:
        with get_db() as cur:
            # 1. Create Tables
            cur.execute(schema_sql)
            print("✅ Tables created successfully.")

            # 2. Ensure at least one Shop exists (Shop ID 1)
            cur.execute("SELECT id FROM shops WHERE id = 1")
            if not cur.fetchone():
                cur.execute("INSERT INTO shops (id, name) VALUES (1, 'Main Barbershop')")
                print("✅ Default Shop created.")
            
            # 3. Ensure at least one Barber exists for Shop 1
            cur.execute("SELECT id FROM barbers WHERE shop_id = 1")
            if not cur.fetchone():
                cur.execute("INSERT INTO barbers (shop_id, display_name) VALUES (1, 'Bosh Usta')")
                print("✅ Default Barber created.")
                
    except Exception as e:
        print(f"❌ Database Init Failed: {e}")

if __name__ == "__main__":
    initialize_production_db()
