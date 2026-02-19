import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
import pytz
from aiogram import Bot
from dotenv import load_dotenv

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../.."))

# Import DB logic
from app.db.conn import get_db
from app.utils.time import get_now, TZ_TASHKENT

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("REMINDER_WORKER")

# Load Env
load_dotenv()

async def send_reminders_task():
    # Load Env inside task to ensure fresh variables if needed
    load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return

    # Create new bot session
    bot = Bot(token=token)
    
    try:
        # Check bookings starting in 1-2 hours
        now = get_now()
        start_window = now + timedelta(hours=1)
        end_window = now + timedelta(hours=2)
        
        # Format for SQL (Timestamptz comparison)
        # Note: psycopg2 handles datetime objects correctly if they have tzinfo.
        
        logger.info(f"Checking reminders for window: {start_window.strftime('%H:%M')} - {end_window.strftime('%H:%M')}")
        
        bookings_to_remind = []
        
        with get_db() as cur:
            # Select CONFIRMED bookings in window that haven't been reminded yet
            cur.execute("""
                SELECT b.id, b.start_at, b.customer_id, c.telegram_user_id, c.full_name, bar.display_name, s.name as service_name
                FROM bookings b
                JOIN customers c ON b.customer_id = c.id
                JOIN barbers bar ON b.barber_id = bar.id
                JOIN services s ON b.service_id = s.id
                WHERE b.status = 'CONFIRMED'
                  AND b.reminded = FALSE
                  AND b.start_at >= %s 
                  AND b.start_at <= %s
            """, (start_window, end_window))
            
            bookings_to_remind = cur.fetchall()

        if not bookings_to_remind:
            logger.info("No bookings found in this window.")
            return

        for b in bookings_to_remind:
            try:
                # Convert time to local string
                local_time = b['start_at'].astimezone(TZ_TASHKENT).strftime("%H:%M")
                
                # Bilingual Reminder Message
                msg_text = (
                    f"🔔 <b>Eslatma / Напоминание!</b>\n\n"
                    f"Hurmatli {b['full_name']},\n"
                    f"Sizning navbatingiz yaqinlashmoqda:\n\n"
                    f"🕒 Vaqt/Время: <b>{local_time}</b>\n"
                    f"💇‍♂️ Usta/Мастер: {b['display_name']}\n"
                    f"✂️ Xizmat/Услуга: {b['service_name']}\n\n"
                    f"📍 Iltimos, kechikmang!\n"
                    f"📍 Пожалуйста, не опаздывайте!"
                )
                
                # Send message
                await bot.send_message(chat_id=b['telegram_user_id'], text=msg_text, parse_mode="HTML")
                
                # Mark as reminded in DB
                with get_db() as cur:
                    cur.execute("UPDATE bookings SET reminded = TRUE WHERE id = %s", (b['id'],))
                
                logger.info(f"Reminder sent to {b['full_name']} (ID: {b['telegram_user_id']}) for booking {b['id']}")
                
            except Exception as e:
                logger.error(f"Failed to send reminder to user {b['telegram_user_id']}: {e}")
                
    except Exception as e:
        logger.error(f"Worker Error: {e}")
    finally:
        # Close bot session to free resources
        await bot.session.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(send_reminders_task())