import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Legion\Documents\barber_booking_bot\.env")

from app.db.conn import get_db

with get_db() as cur:
    cur.execute("SELECT telegram_id, shop_id, id FROM barbers")
    print(cur.fetchall())
    
    owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "")
    print("OWNERS:", owner_ids)
