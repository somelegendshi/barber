import os
import sys
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.join(os.getcwd(), "."))
from app.db.conn import get_db
from app.utils.time import get_now, TZ_TASHKENT
from app.domain.slotting import generate_slots

load_dotenv()

async def run_diagnostics():
    print("--- STARTING DEEP SYSTEM DIAGNOSTICS ---")
    
    with get_db() as cur:
        # 1. ORPHAN CHECK
        print("1. Checking for Integrity Orphans...")
        cur.execute("SELECT id, name FROM shops")
        shops = cur.fetchall()
        for s in shops:
            cur.execute("SELECT count(*) FROM barbers WHERE shop_id = %s", (s['id'],))
            b_count = cur.fetchone()['count']
            cur.execute("SELECT count(*) FROM services WHERE shop_id = %s", (s['id'],))
            s_count = cur.fetchone()['count']
            print(f"   - Shop '{s['name']}' (ID: {s['id']}): {b_count} barbers, {s_count} services.")
            if b_count == 0: print(f"     WARNING: Shop {s['id']} has no barbers.")

        # 2. TIMEZONE & SLOT LOGIC CHECK
        print("\n2. Testing Slot Generation Logic...")
        cur.execute("SELECT * FROM work_hours LIMIT 1")
        wh = cur.fetchone()
        if wh:
            test_date = (get_now() + timedelta(days=1)).date()
            mock_wh = [{'dow': test_date.weekday(), 'start_time': wh['start_time'], 'end_time': wh['end_time'], 'slot_step_min': 30}]
            slots = generate_slots(mock_wh, [], [], 30, test_date)
            print(f"   - Slot generation test: Produced {len(slots)} slots.")
        else:
            print("   - No work_hours found.")

        # 3. OVERLAP PROTECTION CHECK
        print("\n3. Checking for Overlapping Bookings...")
        cur.execute("""
            SELECT b1.id, b2.id 
            FROM bookings b1 
            JOIN bookings b2 ON b1.barber_id = b2.barber_id 
            WHERE b1.id < b2.id 
              AND b1.status = 'CONFIRMED' AND b2.status = 'CONFIRMED'
              AND tstzrange(b1.start_at, b1.end_at) && tstzrange(b2.start_at, b2.end_at)
        """)
        overlaps = cur.fetchall()
        if overlaps:
            print(f"   - BUG FOUND: {len(overlaps)} overlaps!")
        else:
            print("   - No overlaps.")

        # 4. ADMIN COLLISION
        print("\n4. Checking Admin Collision...")
        cur.execute("SELECT telegram_id FROM barbers WHERE telegram_id IS NOT NULL GROUP BY telegram_id HAVING count(*) > 1")
        collisions = cur.fetchall()
        if collisions:
            print("   - BUG FOUND: TG ID collision.")
        else:
            print("   - No collisions.")

    print("\n--- DIAGNOSTICS COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
