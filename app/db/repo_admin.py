from typing import Dict, List, Optional

from app.db.conn import get_db


def add_service_db(shop_id: int, name: str, duration: int):
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Service name cannot be empty.")
    if duration <= 0:
        raise ValueError("Duration must be greater than zero.")

    with get_db() as cur:
        cur.execute(
            "INSERT INTO services (shop_id, name, duration_min) VALUES (%s, %s, %s)",
            (shop_id, clean_name, duration),
        )


def delete_service_db(service_id: int, shop_id: int) -> bool:
    with get_db() as cur:
        cur.execute(
            """
            UPDATE services
            SET is_active = FALSE
            WHERE id = %s AND shop_id = %s AND is_active = TRUE
            RETURNING id
            """,
            (service_id, shop_id),
        )
        return cur.fetchone() is not None


def get_shop_barber_id(shop_id: int) -> Optional[int]:
    with get_db() as cur:
        cur.execute("SELECT id FROM barbers WHERE shop_id = %s ORDER BY id LIMIT 1", (shop_id,))
        res = cur.fetchone()
        return res["id"] if res else None


def ensure_full_week_schedule(barber_id: int) -> List[Dict]:
    with get_db() as cur:
        cur.execute("SELECT dow FROM work_hours WHERE barber_id = %s", (barber_id,))
        existing_dows = {row["dow"] for row in cur.fetchall()}
        for day in range(7):
            if day not in existing_dows:
                cur.execute(
                    """
                    INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min)
                    VALUES (%s, %s, '10:00', '20:00', 30)
                    """,
                    (barber_id, day),
                )

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


def update_day_schedule(barber_id: int, dow: int, start_time: str, end_time: str):
    if start_time == end_time and start_time != "00:00":
        raise ValueError("Start and end time cannot be the same unless the day is closed.")
    if end_time < start_time:
        raise ValueError("Overnight shifts are not supported in the current schedule editor.")

    with get_db() as cur:
        cur.execute(
            "SELECT id FROM work_hours WHERE barber_id = %s AND dow = %s ORDER BY id LIMIT 1",
            (barber_id, dow),
        )
        existing = cur.fetchone()

        if existing:
            cur.execute(
                """
                UPDATE work_hours
                SET start_time = %s, end_time = %s
                WHERE id = %s
                """,
                (start_time, end_time, existing["id"]),
            )
        else:
            cur.execute(
                """
                INSERT INTO work_hours (barber_id, dow, start_time, end_time)
                VALUES (%s, %s, %s, %s)
                """,
                (barber_id, dow, start_time, end_time),
            )


def get_work_hour_by_id(wh_id: int):
    with get_db() as cur:
        cur.execute("SELECT * FROM work_hours WHERE id = %s", (wh_id,))
        return cur.fetchone()
