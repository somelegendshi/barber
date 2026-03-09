import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Legion\Documents\barber_booking_bot\.env")

from app.db.conn import get_db
from app.db.repository import get_work_hours
from app.bot.keyboards import admin_schedule_keyboard
import json

whs = get_work_hours(1)
print(f"WHs for 1: {len(whs)}")

kb = admin_schedule_keyboard(whs)
print(kb.model_dump_json(indent=2))
