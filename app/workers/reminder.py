import asyncio
import logging
import os
import sys
from datetime import timedelta

from aiogram import Bot
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../.."))

from app.db.conn import get_db_connection
from app.utils.text import resolve_lang
from app.utils.time import get_now, to_local

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("REMINDER_WORKER")

load_dotenv()

REMINDER_LOCK_KEY = 9021451


def _try_lock(conn) -> bool:
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT pg_try_advisory_lock(%s) AS locked", (REMINDER_LOCK_KEY,))
            row = cur.fetchone()
            return bool(row and row["locked"])


def _unlock(conn) -> None:
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_unlock(%s)", (REMINDER_LOCK_KEY,))


async def send_reminders_task():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return

    with get_db_connection() as conn:
        lock_acquired = _try_lock(conn)
        if not lock_acquired:
            logger.info("Skipping reminder run because another worker holds the lock.")
            return

        bot = None
        try:
            bot = Bot(token=token)
            now = get_now()
            start_window = now + timedelta(hours=1)
            end_window = now + timedelta(hours=2)
            logger.info(
                "Checking reminders for window: %s - %s",
                start_window.strftime("%H:%M"),
                end_window.strftime("%H:%M"),
            )

            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT
                            b.id,
                            b.start_at,
                            c.telegram_user_id,
                            c.full_name,
                            c.language_code,
                            bar.display_name,
                            s.name AS service_name,
                            sh.timezone AS shop_timezone
                        FROM bookings b
                        JOIN customers c ON b.customer_id = c.id
                        JOIN barbers bar ON b.barber_id = bar.id
                        JOIN services s ON b.service_id = s.id
                        JOIN shops sh ON b.shop_id = sh.id
                        WHERE b.status = 'CONFIRMED'
                          AND b.reminded = FALSE
                          AND b.start_at >= %s
                          AND b.start_at <= %s
                        ORDER BY b.start_at
                        """,
                        (start_window, end_window),
                    )
                    bookings_to_remind = cur.fetchall()

            if not bookings_to_remind:
                logger.info("No bookings found in this window.")
                return

            for booking in bookings_to_remind:
                try:
                    local_time = to_local(booking["start_at"], booking["shop_timezone"]).strftime("%H:%M")
                    lang = resolve_lang(booking.get("language_code"))
                    if lang == "ru":
                        msg_text = (
                            "<b>Napominanie!</b>\n\n"
                            f"{booking['full_name']}, vasha zapis' skoro nachnetsya.\n\n"
                            f"Time: <b>{local_time}</b>\n"
                            f"Master: {booking['display_name']}\n"
                            f"Service: {booking['service_name']}\n\n"
                            "Pozhaluysta, ne opazdyvaite."
                        )
                    else:
                        msg_text = (
                            "<b>Eslatma!</b>\n\n"
                            f"{booking['full_name']}, navbatingiz yaqinlashmoqda.\n\n"
                            f"Vaqt: <b>{local_time}</b>\n"
                            f"Usta: {booking['display_name']}\n"
                            f"Xizmat: {booking['service_name']}\n\n"
                            "Iltimos, kechikmang."
                        )
                    await bot.send_message(chat_id=booking["telegram_user_id"], text=msg_text, parse_mode="HTML")
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE bookings SET reminded = TRUE WHERE id = %s AND reminded = FALSE",
                                (booking["id"],),
                            )
                    logger.info(
                        "Reminder sent to %s (ID: %s) for booking %s",
                        booking["full_name"],
                        booking["telegram_user_id"],
                        booking["id"],
                    )
                except Exception as exc:
                    logger.error(
                        "Failed to send reminder to user %s: %s",
                        booking["telegram_user_id"],
                        exc,
                    )
        except Exception as exc:
            logger.error("Worker error: %s", exc)
        finally:
            try:
                _unlock(conn)
            except Exception as exc:
                logger.error("Failed to release reminder lock: %s", exc)
            if bot is not None:
                await bot.session.close()


async def run_reminder_loop(interval_seconds: int = 15 * 60):
    while True:
        try:
            await send_reminders_task()
            await asyncio.sleep(interval_seconds)
        except Exception as exc:
            logger.error("Reminder loop error: %s", exc)
            await asyncio.sleep(60)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(send_reminders_task())
