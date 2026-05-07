import datetime
import logging
from typing import Dict, List, Optional

import psycopg2

from app.utils.text import normalize_language_code
from app.utils.time import combine_date_time, get_now

from .conn import get_db

logger = logging.getLogger(__name__)


def get_shop(shop_id: int) -> Optional[Dict]:
    with get_db() as cur:
        cur.execute("SELECT * FROM shops WHERE id = %s", (shop_id,))
        return cur.fetchone()


def get_shop_by_public_code(public_code: int) -> Optional[Dict]:
    with get_db() as cur:
        cur.execute("SELECT * FROM shops WHERE public_code = %s", (public_code,))
        return cur.fetchone()


def resolve_shop_reference(shop_reference: int) -> Optional[Dict]:
    shop = get_shop_by_public_code(shop_reference)
    if shop:
        return shop
    return get_shop(shop_reference)


def list_shops() -> List[Dict]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT id, public_code, name, timezone, created_at
            FROM shops
            ORDER BY public_code, id
            """
        )
        return cur.fetchall()


def list_services(shop_id: int) -> List[Dict]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT id, name, duration_min
            FROM services
            WHERE shop_id = %s AND is_active = TRUE
            ORDER BY id
            """,
            (shop_id,),
        )
        return cur.fetchall()


def get_service(service_id: int, shop_id: Optional[int] = None) -> Optional[Dict]:
    query = """
        SELECT id, shop_id, name, duration_min
        FROM services
        WHERE id = %s AND is_active = TRUE
    """
    params: List[int] = [service_id]
    if shop_id is not None:
        query += " AND shop_id = %s"
        params.append(shop_id)

    with get_db() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchone()


def list_barbers(shop_id: int) -> List[Dict]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT id, display_name
            FROM barbers
            WHERE shop_id = %s AND is_active = TRUE
            ORDER BY display_name
            """,
            (shop_id,),
        )
        return cur.fetchall()


def get_barber(barber_id: int, shop_id: Optional[int] = None) -> Optional[Dict]:
    query = """
        SELECT id, shop_id, display_name, telegram_id, notify_telegram_id, is_active
        FROM barbers
        WHERE id = %s AND is_active = TRUE
    """
    params: List[int] = [barber_id]
    if shop_id is not None:
        query += " AND shop_id = %s"
        params.append(shop_id)

    with get_db() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchone()


def list_barbers_admin(
    shop_id: int,
    now_dt: Optional[datetime.datetime] = None,
) -> List[Dict]:
    now_dt = now_dt or get_now()
    with get_db() as cur:
        cur.execute(
            """
            SELECT
                bar.id,
                bar.display_name,
                bar.notify_telegram_id,
                bar.is_active,
                EXISTS (
                    SELECT 1
                    FROM bookings b
                    WHERE b.barber_id = bar.id
                      AND b.status = 'CONFIRMED'
                      AND b.start_at >= %s
                ) AS has_future_bookings
            FROM barbers bar
            WHERE bar.shop_id = %s
            ORDER BY bar.is_active DESC, bar.display_name
            """,
            (now_dt, shop_id),
        )
        return cur.fetchall()


def get_work_hours(barber_id: int) -> List[Dict]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT id, dow, start_time, end_time, slot_step_min
            FROM work_hours
            WHERE barber_id = %s
            ORDER BY dow, start_time
            """,
            (barber_id,),
        )
        return cur.fetchall()


def ensure_customer(
    telegram_user_id: int,
    name: str,
    phone: Optional[str] = None,
    username: Optional[str] = None,
    language_code: Optional[str] = None,
):
    language_code = normalize_language_code(language_code)
    fields = ["telegram_user_id", "full_name"]
    values: List[object] = [telegram_user_id, name]
    updates = ["full_name = EXCLUDED.full_name"]

    if phone is not None:
        fields.append("phone")
        values.append(phone)
        updates.append("phone = EXCLUDED.phone")

    if username is not None:
        fields.append("username")
        values.append(username)
        updates.append("username = EXCLUDED.username")

    if language_code is not None:
        fields.append("language_code")
        values.append(language_code)
        updates.append("language_code = EXCLUDED.language_code")

    fields_sql = ", ".join(fields)
    placeholders_sql = ", ".join(["%s"] * len(values))
    updates_sql = ",\n                    ".join(updates)

    with get_db() as cur:
        cur.execute(
            f"""
            INSERT INTO customers ({fields_sql})
            VALUES ({placeholders_sql})
            ON CONFLICT (telegram_user_id) DO UPDATE
            SET {updates_sql}
            RETURNING id
            """,
            tuple(values),
        )
        return cur.fetchone()["id"]


def get_customer_phone(telegram_user_id: int) -> Optional[str]:
    with get_db() as cur:
        cur.execute("SELECT phone FROM customers WHERE telegram_user_id = %s", (telegram_user_id,))
        row = cur.fetchone()
        return row["phone"] if row else None


def get_customer_language(telegram_user_id: int) -> Optional[str]:
    with get_db() as cur:
        cur.execute("SELECT language_code FROM customers WHERE telegram_user_id = %s", (telegram_user_id,))
        row = cur.fetchone()
        return normalize_language_code(row["language_code"]) if row else None


def set_customer_language(
    telegram_user_id: int,
    name: str,
    language_code: str,
    username: Optional[str] = None,
) -> int:
    return ensure_customer(
        telegram_user_id,
        name,
        username=username,
        language_code=language_code,
    )


def get_bookings(
    shop_id: int,
    barber_id: int,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
) -> List[Dict]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT start_at, end_at
            FROM bookings
            WHERE shop_id = %s
              AND barber_id = %s
              AND status = 'CONFIRMED'
              AND start_at < %s
              AND end_at > %s
            ORDER BY start_at
            """,
            (shop_id, barber_id, end_dt, start_dt),
        )
        return cur.fetchall()


def get_time_off(
    barber_id: int,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
) -> List[Dict]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT start_at, end_at, reason
            FROM time_off
            WHERE barber_id = %s
              AND start_at < %s
              AND end_at > %s
            ORDER BY start_at
            """,
            (barber_id, end_dt, start_dt),
        )
        return cur.fetchall()


def list_bookings_detailed(
    shop_id: int,
    date_value: datetime.date,
    timezone_name: str = "Asia/Tashkent",
) -> List[Dict]:
    start_dt = combine_date_time(date_value, datetime.time.min, timezone_name)
    end_dt = combine_date_time(date_value, datetime.time.max, timezone_name)

    with get_db() as cur:
        cur.execute(
            """
            SELECT
                b.id,
                b.customer_name,
                b.start_at,
                bar.display_name AS barber_name,
                s.name AS service_name,
                c.phone AS customer_phone,
                c.username AS customer_username
            FROM bookings b
            JOIN barbers bar ON b.barber_id = bar.id
            JOIN services s ON b.service_id = s.id
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE b.shop_id = %s
              AND b.status = 'CONFIRMED'
              AND b.start_at < %s
              AND b.end_at > %s
            ORDER BY b.start_at ASC
            """,
            (shop_id, end_dt, start_dt),
        )
        return cur.fetchall()


def list_confirmed_bookings_from(
    shop_id: int,
    start_dt: datetime.datetime,
) -> List[Dict]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT
                b.id,
                b.customer_name,
                b.start_at,
                bar.display_name AS barber_name,
                s.name AS service_name,
                c.phone AS customer_phone,
                c.username AS customer_username
            FROM bookings b
            JOIN barbers bar ON b.barber_id = bar.id
            JOIN services s ON b.service_id = s.id
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE b.shop_id = %s
              AND b.status = 'CONFIRMED'
              AND b.start_at >= %s
            ORDER BY b.start_at ASC
            """,
            (shop_id, start_dt),
        )
        return cur.fetchall()


def list_all_future_bookings(
    shop_id: int,
    now_dt: Optional[datetime.datetime] = None,
) -> List[Dict]:
    return list_confirmed_bookings_from(shop_id, now_dt or get_now())


def cancel_booking_db(booking_id: int, shop_id: int) -> bool:
    with get_db() as cur:
        cur.execute(
            """
            UPDATE bookings
            SET status = 'CANCELLED'
            WHERE id = %s AND shop_id = %s AND status = 'CONFIRMED'
            RETURNING id
            """,
            (booking_id, shop_id),
        )
        return cur.fetchone() is not None


def cancel_booking_by_customer(booking_id: int, telegram_user_id: int) -> bool:
    with get_db() as cur:
        cur.execute(
            """
            UPDATE bookings AS b
            SET status = 'CANCELLED'
            FROM customers AS c
            WHERE b.customer_id = c.id
              AND b.id = %s
              AND c.telegram_user_id = %s
              AND b.status = 'CONFIRMED'
            RETURNING b.id
            """,
            (booking_id, telegram_user_id),
        )
        return cur.fetchone() is not None


def get_customer_booking_for_notification(booking_id: int, telegram_user_id: int) -> Optional[Dict]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT
                b.id,
                b.shop_id,
                b.barber_id,
                b.start_at,
                b.customer_name,
                sh.name AS shop_name,
                sh.timezone AS shop_timezone,
                bar.display_name AS barber_name,
                bar.notify_telegram_id,
                s.name AS service_name,
                c.phone AS customer_phone
            FROM bookings b
            JOIN customers c ON b.customer_id = c.id
            JOIN shops sh ON b.shop_id = sh.id
            JOIN barbers bar ON b.barber_id = bar.id
            JOIN services s ON b.service_id = s.id
            WHERE b.id = %s
              AND c.telegram_user_id = %s
              AND b.status = 'CONFIRMED'
            LIMIT 1
            """,
            (booking_id, telegram_user_id),
        )
        return cur.fetchone()


def block_time_range(
    barber_id: int,
    start_at: datetime.datetime,
    end_at: datetime.datetime,
    reason: str = "Manual Block",
):
    with get_db() as cur:
        cur.execute(
            """
            INSERT INTO time_off (barber_id, start_at, end_at, reason)
            VALUES (%s, %s, %s, %s)
            """,
            (barber_id, start_at, end_at, reason),
        )


def list_customer_bookings(
    telegram_user_id: int,
    shop_id: Optional[int] = None,
    now_dt: Optional[datetime.datetime] = None,
) -> List[Dict]:
    now_dt = now_dt or get_now()
    query = """
        SELECT
            b.id,
            b.start_at,
            sh.name AS shop_name,
            sh.timezone AS shop_timezone,
            bar.display_name AS barber_name,
            s.name AS service_name
        FROM bookings b
        JOIN barbers bar ON b.barber_id = bar.id
        JOIN services s ON b.service_id = s.id
        JOIN shops sh ON b.shop_id = sh.id
        JOIN customers c ON b.customer_id = c.id
        WHERE c.telegram_user_id = %s
          AND b.status = 'CONFIRMED'
          AND b.start_at >= %s
    """
    params: List[object] = [telegram_user_id, now_dt]
    if shop_id is not None:
        query += " AND b.shop_id = %s"
        params.append(shop_id)

    query += " ORDER BY b.start_at ASC"
    with get_db() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def insert_booking(booking_data: Dict) -> Optional[int]:
    try:
        with get_db() as cur:
            cur.execute(
                """
                INSERT INTO bookings (
                    shop_id,
                    barber_id,
                    service_id,
                    customer_id,
                    customer_name,
                    start_at,
                    end_at,
                    status
                )
                VALUES (
                    %(shop_id)s,
                    %(barber_id)s,
                    %(service_id)s,
                    %(customer_id)s,
                    %(customer_name)s,
                    %(start_at)s,
                    %(end_at)s,
                    'CONFIRMED'
                )
                RETURNING id
                """,
                booking_data,
            )
            row = cur.fetchone()
            return row["id"]
    except psycopg2.IntegrityError:
        logger.warning(
            "Booking overlap detected for barber %s at %s",
            booking_data["barber_id"],
            booking_data["start_at"],
        )
        return None
    except Exception as exc:
        logger.error("Booking failed (unexpected): %s", exc)
        return None


def assign_shop_admin(shop_id: int, telegram_id: int) -> bool:
    with get_db() as cur:
        cur.execute(
            """
            SELECT shop_id
            FROM shop_admins
            WHERE telegram_id = %s
              AND shop_id <> %s
            LIMIT 1
            """,
            (telegram_id, shop_id),
        )
        if cur.fetchone():
            raise ValueError("This Telegram ID is already assigned to another shop admin.")

        cur.execute(
            """
            INSERT INTO shop_admins (shop_id, telegram_id, role)
            VALUES (%s, %s, 'admin')
            ON CONFLICT (shop_id, telegram_id) DO NOTHING
            RETURNING shop_id
            """,
            (shop_id, telegram_id),
        )
        return True


def create_shop_db(name: str) -> int:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Shop name cannot be empty.")

    with get_db() as cur:
        cur.execute("INSERT INTO shops (name) VALUES (%s) RETURNING id", (clean_name,))
        return cur.fetchone()["id"]


def delete_shop_db(shop_id: int) -> bool:
    with get_db() as cur:
        cur.execute("DELETE FROM shops WHERE id = %s RETURNING id", (shop_id,))
        return cur.fetchone() is not None


def create_default_shop_services(shop_id: int):
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM services WHERE shop_id = %s", (shop_id,))
        if cur.fetchone()["total"] > 0:
            return

        cur.execute(
            """
            INSERT INTO services (shop_id, name, duration_min)
            VALUES
            (%s, 'Soch olish / Стрижка', 30),
            (%s, 'Soqol olish / Стрижка бороды', 20)
            """,
            (shop_id, shop_id),
        )


def assign_barber_notification_id(barber_id: int, telegram_id: int) -> bool:
    with get_db() as cur:
        cur.execute(
            """
            UPDATE barbers
            SET notify_telegram_id = %s
            WHERE id = %s AND is_active = TRUE
            RETURNING id
            """,
            (telegram_id, barber_id),
        )
        return cur.fetchone() is not None


def get_admin_shop_id(telegram_id: int) -> Optional[int]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT DISTINCT shop_id
            FROM shop_admins
            WHERE telegram_id = %s
            ORDER BY shop_id
            """,
            (telegram_id,),
        )
        rows = cur.fetchall()

    if not rows:
        return None
    if len(rows) > 1:
        logger.error("Telegram ID %s is linked to multiple shops.", telegram_id)
        return None
    return rows[0]["shop_id"]


def list_shop_admin_ids(shop_id: int) -> List[int]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT DISTINCT telegram_id
            FROM shop_admins
            WHERE shop_id = %s
            ORDER BY telegram_id
            """,
            (shop_id,),
        )
        return [row["telegram_id"] for row in cur.fetchall()]


def list_booking_notification_ids(shop_id: int, barber_id: int) -> List[int]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT DISTINCT recipient_id
            FROM (
                SELECT telegram_id AS recipient_id
                FROM shop_admins
                WHERE shop_id = %s
                UNION
                SELECT notify_telegram_id AS recipient_id
                FROM barbers
                WHERE id = %s
                  AND notify_telegram_id IS NOT NULL
            ) AS recipients
            ORDER BY recipient_id
            """,
            (shop_id, barber_id),
        )
        return [row["recipient_id"] for row in cur.fetchall()]


def get_shop_owner_id(shop_id: int) -> Optional[int]:
    admin_ids = list_shop_admin_ids(shop_id)
    return admin_ids[0] if admin_ids else None


def sync_table_id_sequence(table_name: str) -> None:
    with get_db() as cur:
        cur.execute(f"SELECT COALESCE(MAX(id), 0) AS max_id FROM {table_name}")
        max_id = cur.fetchone()["max_id"]
        sequence_name = f"{table_name}_id_seq"
        if max_id > 0:
            cur.execute("SELECT setval(%s::regclass, %s, true)", (sequence_name, max_id))
        else:
            cur.execute("SELECT setval(%s::regclass, %s, false)", (sequence_name, 1))


def sync_core_id_sequences() -> None:
    for table_name in ["shops", "barbers", "services", "bookings", "customers", "work_hours", "time_off"]:
        sync_table_id_sequence(table_name)
    sync_shop_public_code_sequence()


def sync_shop_public_code_sequence() -> None:
    with get_db() as cur:
        cur.execute("SELECT COALESCE(MAX(public_code), 0) AS max_code FROM shops")
        max_code = cur.fetchone()["max_code"]
        if max_code > 0:
            cur.execute("SELECT setval('shops_public_code_seq'::regclass, %s, true)", (max_code,))
        else:
            cur.execute("SELECT setval('shops_public_code_seq'::regclass, %s, false)", (1,))


def _legacy_add_barber_db(shop_id: int, name: str) -> int:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Barber name cannot be empty.")

    with get_db() as cur:
        cur.execute(
            "INSERT INTO barbers (shop_id, display_name) VALUES (%s, %s) RETURNING id",
            (shop_id, clean_name),
        )
        barber_id = cur.fetchone()["id"]

        cur.execute(
            """
            INSERT INTO services (shop_id, name, duration_min)
            VALUES
            (%s, 'Soch olish / Стрижка', 30),
            (%s, 'Soqol olish / Стрижка бороды', 20)
            """,
            (shop_id, shop_id),
        )

        for day in range(7):
            cur.execute(
                """
                INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min)
                VALUES (%s, %s, '10:00', '20:00', 30)
                """,
                (barber_id, day),
            )
        return barber_id


def add_barber_db(shop_id: int, name: str) -> int:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Barber name cannot be empty.")

    with get_db() as cur:
        cur.execute(
            "INSERT INTO barbers (shop_id, display_name) VALUES (%s, %s) RETURNING id",
            (shop_id, clean_name),
        )
        barber_id = cur.fetchone()["id"]

        for day in range(7):
            cur.execute(
                """
                INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min)
                VALUES (%s, %s, '10:00', '20:00', 30)
                """,
                (barber_id, day),
            )
        return barber_id


def deactivate_barber_db(shop_id: int, barber_id: int) -> Optional[str]:
    with get_db() as cur:
        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM barbers
            WHERE shop_id = %s AND is_active = TRUE
            """,
            (shop_id,),
        )
        if cur.fetchone()["total"] <= 1:
            raise ValueError("At least one active barber must remain in the shop.")

        cur.execute(
            """
            SELECT telegram_id
            FROM barbers
            WHERE id = %s AND shop_id = %s AND is_active = TRUE
            """,
            (barber_id, shop_id),
        )
        barber_row = cur.fetchone()
        if not barber_row:
            return None

        cur.execute(
            """
            SELECT 1
            FROM bookings
            WHERE barber_id = %s
              AND status = 'CONFIRMED'
              AND start_at >= %s
            LIMIT 1
            """,
            (barber_id, get_now()),
        )
        if cur.fetchone():
            raise ValueError("This barber still has upcoming bookings.")

        cur.execute(
            """
            UPDATE barbers
            SET is_active = FALSE,
                telegram_id = NULL,
                notify_telegram_id = NULL
            WHERE id = %s AND shop_id = %s AND is_active = TRUE
            RETURNING display_name
            """,
            (barber_id, shop_id),
        )
        row = cur.fetchone()
        return row["display_name"] if row else None
