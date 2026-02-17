import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
import os
import sys
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Auto-Initialize Database for Production
from app.scripts.init_db import initialize_production_db
initialize_production_db()

# Import handlers
from app.bot import handlers_start, handlers_booking, handlers_owner, handlers_customer, handlers_super_admin, handlers_admin_settings
from app.bot.middleware import GlobalErrorHandler

# Import reminder worker
from app.workers.reminder import send_reminders_task

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_reminder_loop():
    """Background task that runs every 15 minutes."""
    while True:
        try:
            logger.info("⏳ Running periodic reminder check...")
            await send_reminders_task()
            await asyncio.sleep(15 * 60)
        except Exception as e:
            logger.error(f"Reminder loop error: {e}")
            await asyncio.sleep(60)

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in environment")
    
    # Initialize Bot & Dispatcher
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register Middleware
    dp.message.outer_middleware(GlobalErrorHandler())
    dp.callback_query.outer_middleware(GlobalErrorHandler())
    
    # Register Routers
    dp.include_router(handlers_super_admin.router)
    dp.include_router(handlers_admin_settings.router)
    dp.include_router(handlers_start.router)
    dp.include_router(handlers_booking.router)
    dp.include_router(handlers_customer.router)
    dp.include_router(handlers_owner.router)

    # Run reminder task in background
    loop_task = asyncio.create_task(start_reminder_loop())
    
    logger.info("🚀 Bot is starting...")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Polling error: {e}")
    finally:
        loop_task.cancel()
        await bot.session.close()

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
