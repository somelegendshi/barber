import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Legion\Documents\barber_booking_bot\.env")

from app.db.conn import get_db

with get_db() as cur:
    cur.execute("SELECT * FROM shops")
    print("Shops:", [dict(s) for s in cur.fetchall()])
    
    cur.execute("SELECT id, display_name, shop_id, telegram_id FROM barbers")
    print("Barbers:", [dict(b) for b in cur.fetchall()])
    
    cur.execute("SELECT barber_id, count(*) as count FROM work_hours GROUP BY barber_id")
    print("Work Hours:", [dict(w) for w in cur.fetchall()])
