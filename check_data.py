import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "."))

from app.db.conn import get_db

load_dotenv()

def check_bookings():
    with get_db() as cur:
        print("--- ALL SHOPS ---")
        cur.execute("SELECT id, name FROM shops")
        for s in cur.fetchall():
            print(f"Shop ID: {s['id']}, Name: {s['name']}")
            
        print("\n--- ALL BARBERS ---")
        cur.execute("SELECT id, shop_id, display_name FROM barbers")
        for b in cur.fetchall():
            print(f"Barber ID: {b['id']}, Shop ID: {b['shop_id']}, Name: {b['display_name']}")

        print("\n--- RECENT CONFIRMED BOOKINGS (Last 5) ---")
        cur.execute("""
            SELECT b.id, b.shop_id, b.barber_id, b.customer_name, b.start_at, b.status 
            FROM bookings b 
            ORDER BY b.id DESC LIMIT 5
        """)
        for b in cur.fetchall():
            try:
                print(f"ID: {b['id']}, Shop: {b['shop_id']}, Barber: {b['barber_id']}, Name: {b['customer_name']}, Start: {b['start_at']}, Status: {b['status']}")
            except:
                print(f"ID: {b['id']}, Shop: {b['shop_id']} - (Unicode Error in Name)")

if __name__ == "__main__":
    check_bookings()
