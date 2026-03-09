import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Legion\Documents\barber_booking_bot\.env")

from app.db.conn import get_db

with get_db() as cur:
    cur.execute("SELECT * FROM barbers")
    barbers = cur.fetchall()
    print("Barbers:", [dict(b) for b in barbers])
    
    cur.execute("SELECT barber_id, count(*) as c FROM work_hours GROUP BY barber_id")
    whs = cur.fetchall()
    print("WHs:", [dict(w) for w in whs])
