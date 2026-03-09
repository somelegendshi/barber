import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Legion\Documents\barber_booking_bot\.env")

from app.db.conn import get_db
from app.db.repository import get_work_hours
from app.bot.keyboards import admin_schedule_keyboard

wh = get_work_hours(1)
kb = admin_schedule_keyboard(wh)

for row in kb.inline_keyboard:
    print([b.text for b in row])
