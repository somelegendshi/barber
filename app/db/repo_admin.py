from typing import List, Dict, Optional
import datetime
from app.db.conn import get_db

def add_service_db(shop_id: int, name: str, duration: int):
    with get_db() as cur:
        cur.execute(
            "INSERT INTO services (shop_id, name, duration_min) VALUES (%s, %s, %s)",
            (shop_id, name, duration)
        )

def delete_service_db(service_id: int, shop_id: int):
    with get_db() as cur:
        cur.execute(
            "DELETE FROM services WHERE id = %s AND shop_id = %s",
            (service_id, shop_id)
        )

def get_shop_barber_id(shop_id: int) -> int:
    """Get the main barber ID for a shop."""
    with get_db() as cur:
        cur.execute("SELECT id FROM barbers WHERE shop_id = %s LIMIT 1", (shop_id,))
        res = cur.fetchone()
        return res['id'] if res else None

def update_day_schedule(barber_id: int, dow: int, start_time: str, end_time: str):
    with get_db() as cur:
        cur.execute(
            "SELECT id FROM work_hours WHERE barber_id = %s AND dow = %s",
            (barber_id, dow)
        )
        existing = cur.fetchone()
        
        if existing:
            cur.execute("""
                UPDATE work_hours 
                SET start_time = %s, end_time = %s 
                WHERE id = %s
            """, (start_time, end_time, existing['id']))
        else:
            cur.execute("""
                INSERT INTO work_hours (barber_id, dow, start_time, end_time)
                VALUES (%s, %s, %s, %s)
            """, (barber_id, dow, start_time, end_time))

def get_work_hour_by_id(wh_id: int):
    with get_db() as cur:
        cur.execute("SELECT * FROM work_hours WHERE id = %s", (wh_id,))
        return cur.fetchone()

# FIXED: Fallback logic for Shop Owner check
def get_current_shop_id_fixed(user_id: int) -> int:
    with get_db() as cur:
        # Check if this user is a barber/admin of ANY shop
        cur.execute("SELECT shop_id FROM barbers WHERE telegram_id = %s LIMIT 1", (user_id,))
        res = cur.fetchone()
        if res:
            return res['shop_id']
        
        # If not an admin, default to shop 1
        return 1
