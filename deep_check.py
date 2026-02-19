import os
import sys
from dotenv import load_dotenv
import datetime

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "."))

from app.db.conn import get_db

load_dotenv()

def deep_check():
    with get_db() as cur:
        print("--- SERVER TIME INFO ---")
        cur.execute("SELECT NOW(), NOW() AT TIME ZONE 'Asia/Tashkent' as local_now")
        time_info = cur.fetchone()
        print(f"Server Now: {time_info['now']}")
        print(f"Tashkent Now: {time_info['local_now']}")

        print("\n--- ALL BOOKINGS RAW (SAFE PRINT) ---")
        cur.execute("SELECT id, shop_id, start_at, status FROM bookings")
        bookings = cur.fetchall()
        if not bookings:
            print("DATABASE IS EMPTY.")
        for b in bookings:
            print(f"ID: {b['id']}, Shop: {b['shop_id']}, Start: {b['start_at']}, Status: {b['status']}")

if __name__ == "__main__":
    deep_check()
