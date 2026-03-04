import asyncio
import os
import sys
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Setup Environment
sys.path.append(os.getcwd())
load_dotenv()

from app.db.conn import get_db
from app.db.repository import (
    get_shop, list_services, list_barbers, get_work_hours, 
    ensure_customer, insert_booking, get_bookings
)
from app.domain.slotting import generate_slots

# Constants
TEST_USER_ID = 999999
TEST_SHOP_ID = 1
TZ = pytz.timezone("Asia/Tashkent")

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def clean_db():
    with get_db() as cur:
        cur.execute("DELETE FROM bookings WHERE customer_id IN (SELECT id FROM customers WHERE telegram_user_id = %s)", (TEST_USER_ID,))
        cur.execute("DELETE FROM customers WHERE telegram_user_id = %s", (TEST_USER_ID,))
    log("Cleaned up previous test data.", "SETUP")

def test_flow():
    # 1. Setup User
    log("Creating Test User...", "STEP 1")
    customer_id = ensure_customer(TEST_USER_ID, "Test User", "+998901234567", "test_user")
    if not customer_id:
        log("Failed to create customer", "FAIL")
        return
    log(f"Customer created/found. ID: {customer_id}", "PASS")

    # 2. List Services & Barbers
    log("Fetching Shop Data...", "STEP 2")
    services = list_services(TEST_SHOP_ID)
    barbers = list_barbers(TEST_SHOP_ID)
    
    if not services:
        log("No services found!", "FAIL")
        return
    if not barbers:
        log("No barbers found!", "FAIL")
        return
    
    service = services[0]
    barber = barbers[0]
    log(f"Selected Service: {service['name']} ({service['duration_min']} min)", "INFO")
    log(f"Selected Barber: {barber['display_name']}", "INFO")

    # 3. Check Slots (Timezone Logic)
    log("Checking Availability (Timezone Test)...", "STEP 3")
    tomorrow = datetime.now(TZ).date() + timedelta(days=1)
    
    work_hours = get_work_hours(barber['id'])
    
    # Get Bookings for tomorrow
    start_dt = TZ.localize(datetime.combine(tomorrow, datetime.min.time()))
    end_dt = TZ.localize(datetime.combine(tomorrow, datetime.max.time()))
    existing_bookings = get_bookings(TEST_SHOP_ID, barber['id'], start_dt, end_dt)
    
    # Generate Slots
    naive_bookings = [{'start_at': b['start_at'].astimezone(TZ).replace(tzinfo=None), 'end_at': b['end_at'].astimezone(TZ).replace(tzinfo=None)} for b in existing_bookings]
    slots = generate_slots(work_hours, naive_bookings, [], service['duration_min'], tomorrow)
    
    if not slots:
        log("No slots available for tomorrow. Cannot test booking.", "WARN")
        return

    target_time = slots[0] # Pick first available slot
    log(f"Target Slot found: {tomorrow} at {target_time.strftime('%H:%M')}", "PASS")

    # 4. Make Booking
    log("Attempting Booking...", "STEP 4")
    booking_start = TZ.localize(datetime.combine(tomorrow, target_time))
    booking_end = booking_start + timedelta(minutes=service['duration_min'])
    
    booking_data = {
        "shop_id": TEST_SHOP_ID,
        "barber_id": barber['id'],
        "service_id": service['id'],
        "customer_id": customer_id,
        "customer_name": "Test User",
        "start_at": booking_start,
        "end_at": booking_end
    }
    
    booking_id = insert_booking(booking_data)
    
    if booking_id:
        log(f"Booking created successfully! ID: {booking_id}", "PASS")
    else:
        log("Failed to create booking!", "FAIL")
        return

    # 5. Verify in DB
    with get_db() as cur:
        cur.execute("SELECT start_at FROM bookings WHERE id = %s", (booking_id,))
        saved_dt = cur.fetchone()['start_at']
        # Check if saved time matches (handling Postgres return format)
        if saved_dt.astimezone(TZ) == booking_start:
             log(f"DB Timestamp Verification: Correct ({saved_dt})", "PASS")
        else:
             log(f"DB Timestamp Mismatch! Sent: {booking_start}, Got: {saved_dt}", "FAIL")

    # 6. Test Double Booking Protection
    log("Testing Double Booking Protection...", "STEP 6")
    duplicate_id = insert_booking(booking_data)
    
    if duplicate_id is None:
        log("System correctly rejected double booking.", "PASS")
    else:
        log(f"CRITICAL: Double booking allowed! ID: {duplicate_id}", "FAIL")

if __name__ == "__main__":
    try:
        clean_db()
        test_flow()
        clean_db() # Cleanup after test
    except Exception as e:
        log(f"Test Crashed: {e}", "CRITICAL")
