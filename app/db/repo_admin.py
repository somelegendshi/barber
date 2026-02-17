from typing import List, Dict, Optional
import datetime
from app.db.conn import get_db

# ... (existing functions)

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

def update_work_hours_db(barber_id: int, dow: int, start_time: str, end_time: str):
    # This assumes 1 barber per shop for now (Simple SaaS)
    # We need to find the barber_id for the shop first usually, but assuming we pass it.
    with get_db() as cur:
        cur.execute("""
            INSERT INTO work_hours (barber_id, dow, start_time, end_time)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE -- Wait, schema might not have unique constraint on (barber_id, dow)
            -- Ideally we Update based on barber_id + dow
            -- Let's check schema. We might need to Delete + Insert or Update where barber_id & dow.
        """, (barber_id, dow, start_time, end_time))

def get_shop_barber_id(shop_id: int) -> int:
    """Get the main barber ID for a shop."""
    with get_db() as cur:
        cur.execute("SELECT id FROM barbers WHERE shop_id = %s LIMIT 1", (shop_id,))
        res = cur.fetchone()
        return res['id'] if res else None

def update_day_schedule(barber_id: int, dow: int, start_time: str, end_time: str):
    with get_db() as cur:
        # Check if row exists
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