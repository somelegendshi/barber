import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Legion\Documents\barber_booking_bot\.env")

from app.db.conn import get_db

with get_db() as cur:
    cur.execute("SELECT * FROM work_hours WHERE barber_id = 1")
    whs = cur.fetchall()
    print("Work hours for barber 1:")
    for w in whs:
        print(w)
    
    cur.execute("SELECT id, display_name FROM barbers")
    barbers = cur.fetchall()
    print("Barbers:", barbers)
