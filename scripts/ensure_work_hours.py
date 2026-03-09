import os
from dotenv import load_dotenv

# Load .env
load_dotenv(r"C:\Users\Legion\Documents\barber_booking_bot\.env")

from app.db.conn import get_db
from app.db.repository import list_barbers, get_work_hours

def ensure_all_work_hours():
    with get_db() as cur:
        # Get all barbers
        cur.execute("SELECT id, shop_id, display_name FROM barbers")
        barbers = cur.fetchall()
        
        for barber in barbers:
            b_id = barber['id']
            # Check if work hours exist
            cur.execute("SELECT count(*) as count FROM work_hours WHERE barber_id = %s", (b_id,))
            count = cur.fetchone()['count']
            
            if count == 0:
                print(f"Adding default work hours for barber {barber['display_name']} (ID {b_id})")
                for day in range(7):
                    cur.execute(
                        "INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) VALUES (%s, %s, '10:00', '20:00', 30)",
                        (b_id, day)
                    )
        print("Done ensuring work hours.")

if __name__ == "__main__":
    ensure_all_work_hours()
