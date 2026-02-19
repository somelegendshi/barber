import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "."))

from app.db.conn import get_db

load_dotenv()

def debug_shop_2():
    with get_db() as cur:
        print("--- CHECKING SHOP 2 ---")
        cur.execute("SELECT * FROM shops WHERE id = 2")
        shop = cur.fetchone()
        if shop:
            print(f"Shop 2 exists: {shop['name']}")
        else:
            print("Shop 2 DOES NOT EXIST in the database!")

        print("\n--- CHECKING BARBERS FOR SHOP 2 ---")
        cur.execute("SELECT * FROM barbers WHERE shop_id = 2")
        barbers = cur.fetchall()
        for b in barbers:
            print(f"Barber ID: {b['id']}, Name: {b['display_name']}, TG_ID: {b['telegram_id']}")

        print("\n--- CHECKING BOOKINGS FOR SHOP 2 ---")
        cur.execute("SELECT * FROM bookings WHERE shop_id = 2")
        bookings = cur.fetchall()
        for b in bookings:
            print(f"Booking ID: {b['id']}, Barber_ID: {b['barber_id']}, Status: {b['status']}, Start: {b['start_at']}")

        print("\n--- CHECKING ALL RECENT BOOKINGS ---")
        cur.execute("SELECT id, shop_id, barber_id, customer_name, status FROM bookings ORDER BY id DESC LIMIT 5")
        for b in cur.fetchall():
            print(f"ID: {b['id']}, Shop: {b['shop_id']}, Barber: {b['barber_id']}, Name: {b['customer_name']}, Status: {b['status']}")

if __name__ == "__main__":
    debug_shop_2()
