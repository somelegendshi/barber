import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Legion\Documents\barber_booking_bot\.env")

from app.db.conn import get_db

with get_db() as cur:
    cur.execute("SELECT id, display_name, shop_id, telegram_id FROM barbers")
    barbers = cur.fetchall()
    
    cur.execute("SELECT barber_id, count(*) as count FROM work_hours GROUP BY barber_id")
    whs = cur.fetchall()

print("Barbers:", [dict(b) for b in barbers])
print("Work Hours per Barber:", [dict(w) for w in whs])
