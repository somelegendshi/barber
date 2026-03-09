import os
import datetime
from app.db.conn import get_db

def fix_work_hours_for_all():
    with get_db() as cur:
        cur.execute("SELECT id FROM barbers")
        barbers = cur.fetchall()
        
        for b in barbers:
            b_id = b['id']
            # Get existing DOWs
            cur.execute("SELECT dow FROM work_hours WHERE barber_id = %s", (b_id,))
            dows = [row['dow'] for row in cur.fetchall()]
            
            # Ensure all 7 days exist
            for day in range(7):
                if day not in dows:
                    cur.execute(
                        "INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) VALUES (%s, %s, '10:00', '20:00', 30)",
                        (b_id, day)
                    )
        print("Ensured all 7 days for all barbers.")

if __name__ == "__main__":
    fix_work_hours_for_all()
