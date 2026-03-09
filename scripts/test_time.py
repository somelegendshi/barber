import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Legion\Documents\barber_booking_bot\.env")

from app.db.conn import get_db
from app.db.repository import get_work_hours

wh = get_work_hours(1)
for w in wh:
    print(type(w['start_time']), w['start_time'])
