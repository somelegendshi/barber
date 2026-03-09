import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Legion\Documents\barber_booking_bot\.env")

from app.db.conn import get_db
from app.db.repository import get_work_hours

with get_db() as cur:
    cur.execute("SELECT id, telegram_id, shop_id FROM barbers")
    print("Barbers:", cur.fetchall())
    
    cur.execute("SELECT * FROM work_hours WHERE barber_id = 1")
    print("WHs for 1:", len(cur.fetchall()))
    
    cur.execute("SELECT * FROM work_hours WHERE barber_id = 2")
    print("WHs for 2:", len(cur.fetchall()))
