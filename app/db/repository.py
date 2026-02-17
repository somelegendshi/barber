from typing import List, Dict, Optional
import datetime
import logging
from .conn import get_db
import psycopg2

logger = logging.getLogger(__name__)

# Fetch shop configuration
def get_shop(shop_id: int) -> Optional[Dict]:
    with get_db() as cur:
        cur.execute("SELECT * FROM shops WHERE id = %s", (shop_id,))
        return cur.fetchone()

# List active services
def list_services(shop_id: int) -> List[Dict]:
    with get_db() as cur:
        cur.execute("""
            SELECT id, name, duration_min 
            FROM services 
            WHERE shop_id = %s AND is_active = TRUE 
            ORDER BY id
        """, (shop_id,))
        return cur.fetchall()

# Get single service details
def get_service(service_id: int) -> Optional[Dict]:
    with get_db() as cur:
        cur.execute("SELECT id, name, duration_min FROM services WHERE id = %s", (service_id,))
        return cur.fetchone()

# List active barbers
def list_barbers(shop_id: int) -> List[Dict]:
    with get_db() as cur:
        cur.execute("""
            SELECT id, display_name 
            FROM barbers 
            WHERE shop_id = %s AND is_active = TRUE 
            ORDER BY display_name
        """, (shop_id,))
        return cur.fetchall()

# Get work hours for a barber
def get_work_hours(barber_id: int) -> List[Dict]:
    with get_db() as cur:
        cur.execute("""
            SELECT dow, start_time, end_time, slot_step_min 
            FROM work_hours 
            WHERE barber_id = %s
        """, (barber_id,))
        return cur.fetchall()

# Ensure customer exists (upsert) - UPDATED FOR PHONE & USERNAME
def ensure_customer(telegram_user_id: int, name: str, phone: str = None, username: str = None):
    with get_db() as cur:
        # If phone provided, update it. If not, keep existing.
        # We handle username update here as well.
        if phone and username:
             cur.execute("""
                INSERT INTO customers (telegram_user_id, full_name, phone, username)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (telegram_user_id) DO UPDATE 
                SET full_name = EXCLUDED.full_name, phone = EXCLUDED.phone, username = EXCLUDED.username
                RETURNING id
            """, (telegram_user_id, name, phone, username))
        elif phone:
            cur.execute("""
                INSERT INTO customers (telegram_user_id, full_name, phone)
                VALUES (%s, %s, %s)
                ON CONFLICT (telegram_user_id) DO UPDATE 
                SET full_name = EXCLUDED.full_name, phone = EXCLUDED.phone
                RETURNING id
            """, (telegram_user_id, name, phone))
        elif username:
             cur.execute("""
                INSERT INTO customers (telegram_user_id, full_name, username)
                VALUES (%s, %s, %s)
                ON CONFLICT (telegram_user_id) DO UPDATE 
                SET full_name = EXCLUDED.full_name, username = EXCLUDED.username
                RETURNING id
            """, (telegram_user_id, name, username))
        else:
            cur.execute("""
                INSERT INTO customers (telegram_user_id, full_name)
                VALUES (%s, %s)
                ON CONFLICT (telegram_user_id) DO UPDATE 
                SET full_name = EXCLUDED.full_name
                RETURNING id
            """, (telegram_user_id, name))
        return cur.fetchone()['id']

# Get customer phone
def get_customer_phone(telegram_user_id: int) -> Optional[str]:
    with get_db() as cur:
        cur.execute("SELECT phone FROM customers WHERE telegram_user_id = %s", (telegram_user_id,))
        row = cur.fetchone()
        return row['phone'] if row else None

# Get confirmed bookings for a date range
def get_bookings(shop_id: int, barber_id: int, start_dt: datetime.datetime, end_dt: datetime.datetime) -> List[Dict]:
    with get_db() as cur:
        cur.execute("""
            SELECT start_at, end_at 
            FROM bookings 
            WHERE shop_id = %s 
              AND barber_id = %s 
              AND status = 'CONFIRMED'
              AND start_at >= %s AND end_at <= %s
        """, (shop_id, barber_id, start_dt, end_dt))
        return cur.fetchall()

# List detailed bookings for owner (e.g. /today)
def list_bookings_detailed(shop_id: int, date: datetime.date) -> List[Dict]:
    start_dt = datetime.datetime.combine(date, datetime.time.min)
    end_dt = datetime.datetime.combine(date, datetime.time.max)
    
    with get_db() as cur:
        cur.execute("""
            SELECT b.id, b.customer_name, b.start_at, bar.display_name as barber_name, s.name as service_name,
                   c.phone as customer_phone, c.username as customer_username
            FROM bookings b
            JOIN barbers bar ON b.barber_id = bar.id
            JOIN services s ON b.service_id = s.id
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE b.shop_id = %s 
              AND b.status = 'CONFIRMED'
              AND b.start_at >= %s AND b.end_at <= %s
            ORDER BY b.start_at ASC
        """, (shop_id, start_dt, end_dt))
        return cur.fetchall()

# List ALL future bookings
# FIXED: Use database time (Asia/Tashkent) to prevent UTC/Server Time issues
def list_all_future_bookings(shop_id: int) -> List[Dict]:
    with get_db() as cur:
        cur.execute("""
            SELECT b.id, b.customer_name, b.start_at, bar.display_name as barber_name, s.name as service_name,
                   c.phone as customer_phone, c.username as customer_username
            FROM bookings b
            JOIN barbers bar ON b.barber_id = bar.id
            JOIN services s ON b.service_id = s.id
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE b.shop_id = %s 
              AND b.status = 'CONFIRMED'
              AND b.start_at >= (NOW() AT TIME ZONE 'Asia/Tashkent')
            ORDER BY b.start_at ASC
        """, (shop_id,))
        return cur.fetchall()

# Cancel booking (Owner only)
def cancel_booking_db(booking_id: int, shop_id: int) -> bool:
    with get_db() as cur:
        cur.execute("""
            UPDATE bookings 
            SET status = 'CANCELLED' 
            WHERE id = %s AND shop_id = %s AND status = 'CONFIRMED'
            RETURNING id
        """, (booking_id, shop_id))
        return cur.fetchone() is not None

# Cancel booking by Customer (with reason)
def cancel_booking_by_customer(booking_id: int, shop_id: int, reason: str) -> bool:
    with get_db() as cur:
        # We could store the reason in a separate log table or just mark cancelled
        # For MVP, we just mark cancelled. If you want to store reason, add a column.
        cur.execute("""
            UPDATE bookings 
            SET status = 'CANCELLED' 
            WHERE id = %s AND shop_id = %s AND status = 'CONFIRMED'
            RETURNING id
        """, (booking_id, shop_id))
        return cur.fetchone() is not None

# Block time range (TimeOff)
def block_time_range(barber_id: int, start_at: datetime.datetime, end_at: datetime.datetime, reason: str = "Manual Block"):
    with get_db() as cur:
        cur.execute("""
            INSERT INTO time_off (barber_id, start_at, end_at, reason)
            VALUES (%s, %s, %s, %s)
        """, (barber_id, start_at, end_at, reason))

# List active bookings for a specific customer (Telegram ID)
# FIXED: Use database time (Asia/Tashkent)
def list_customer_bookings(telegram_user_id: int, shop_id: int) -> List[Dict]:
    with get_db() as cur:
        cur.execute("""
            SELECT b.id, b.start_at, bar.display_name as barber_name, s.name as service_name
            FROM bookings b
            JOIN barbers bar ON b.barber_id = bar.id
            JOIN services s ON b.service_id = s.id
            JOIN customers c ON b.customer_id = c.id
            WHERE c.telegram_user_id = %s
              AND b.shop_id = %s
              AND b.status = 'CONFIRMED'
              AND b.start_at >= (NOW() AT TIME ZONE 'Asia/Tashkent')
            ORDER BY b.start_at ASC
        """, (telegram_user_id, shop_id))
        return cur.fetchall()

# Insert booking safely (atomic transaction)
# FIXED: Handle IntegrityError (Race Condition) gracefully
def insert_booking(booking_data: Dict) -> int:
    try:
        with get_db() as cur:
            cur.execute("""
                INSERT INTO bookings (shop_id, barber_id, service_id, customer_id, customer_name, start_at, end_at, status)
                VALUES (%(shop_id)s, %(barber_id)s, %(service_id)s, %(customer_id)s, %(customer_name)s, %(start_at)s, %(end_at)s, 'CONFIRMED')
                RETURNING id
            """, booking_data)
            row = cur.fetchone()
            return row['id']
    except psycopg2.IntegrityError:
        # This catches the EXCLUDE constraint violation (overlapping booking)
        logger.warning(f"Booking overlap detected for barber {booking_data['barber_id']} at {booking_data['start_at']}")
        return None 
    except Exception as e:
        logger.error(f"Booking failed (unexpected): {e}")
        return None

# --- ADMIN MANAGEMENT ---

def create_shop_db(name: str) -> int:
    with get_db() as cur:
        cur.execute("INSERT INTO shops (name) VALUES (%s) RETURNING id", (name,))
        return cur.fetchone()['id']

def assign_barber_telegram_id(barber_id: int, telegram_id: int) -> bool:
    with get_db() as cur:
        cur.execute("UPDATE barbers SET telegram_id = %s WHERE id = %s", (telegram_id, barber_id))
        return True

def get_admin_shop_id(telegram_id: int) -> Optional[int]:
    """Check if this TG user manages a shop."""
    with get_db() as cur:
        cur.execute("SELECT shop_id FROM barbers WHERE telegram_id = %s LIMIT 1", (telegram_id,))
        res = cur.fetchone()
        return res['shop_id'] if res else None

def get_shop_owner_id(shop_id: int) -> Optional[int]:
    """Get the Telegram ID of the person who should receive notifications for this shop."""
    with get_db() as cur:
        # We assume the first barber added with a telegram_id is the owner
        cur.execute("SELECT telegram_id FROM barbers WHERE shop_id = %s AND telegram_id IS NOT NULL ORDER BY id LIMIT 1", (shop_id,))
        res = cur.fetchone()
        return res['telegram_id'] if res else None

def add_barber_db(shop_id: int, name: str) -> int:
    with get_db() as cur:
        cur.execute(
            "INSERT INTO barbers (shop_id, display_name) VALUES (%s, %s) RETURNING id",
            (shop_id, name)
        )
        barber_id = cur.fetchone()['id']
        
        # Add default services
        cur.execute("""
            INSERT INTO services (shop_id, name, duration_min) 
            VALUES 
            (%s, 'Soch olish / Стрижка', 30), 
            (%s, 'Soqol olish / Стрижка бороды', 20)
        """, (shop_id, shop_id))
        
        # Add default work hours (Mon-Sun 10-20)
        for day in range(7):
            cur.execute(
                "INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) VALUES (%s, %s, '10:00', '20:00', 30)",
                (barber_id, day)
            )
        return barber_id
