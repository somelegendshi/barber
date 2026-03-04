import os
import sys
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.join(os.getcwd(), "."))
from app.db.conn import get_db

load_dotenv()

def test_db_connection():
    try:
        with get_db() as cur:
            cur.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"❌ DB Connection Error: {e}")
        return False

def test_integrity_shops_barbers():
    with get_db() as cur:
        cur.execute("SELECT id FROM shops")
        shops = cur.fetchall()
        for s in shops:
            cur.execute("SELECT id FROM barbers WHERE shop_id = %s", (s['id'],))
            if not cur.fetchall():
                print(f"⚠️ Warning: Shop {s['id']} has no barbers.")
    return True

def run_all_tests():
    print("🧪 --- RUNNING SMOKE TESTS ---")
    
    steps = [
        ("Database Connection", test_db_connection),
        ("Shop-Barber Integrity", test_integrity_shops_barbers)
    ]
    
    all_passed = True
    for name, func in steps:
        if func():
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED")
            all_passed = False
            
    print("🧪 --- TESTS COMPLETE ---")
    return all_passed

if __name__ == "__main__":
    run_all_tests()
