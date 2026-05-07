import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv
from redis.asyncio import Redis

load_dotenv()

from app.scripts.init_db import initialize_production_db

from app.bot import (
    handlers_admin_settings,
    handlers_booking,
    handlers_customer,
    handlers_owner,
    handlers_start,
    handlers_super_admin,
)
from app.bot.middleware import GlobalErrorHandler
from app.workers.reminder import run_reminder_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _is_production_env() -> bool:
    return os.getenv("APP_ENV", "").strip().lower() in {"prod", "production"}


def build_storage():
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        logger.info("Using Redis storage")
        return RedisStorage(redis=Redis.from_url(redis_url))

    if _is_production_env():
        raise ValueError("Missing REDIS_URL while APP_ENV=production")

    logger.warning("Using Memory storage. Configure REDIS_URL before production sale.")
    return MemoryStorage()


async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in environment")

    initialize_production_db()
    storage = build_storage()

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    dp.message.outer_middleware(GlobalErrorHandler())
    dp.callback_query.outer_middleware(GlobalErrorHandler())

    dp.include_router(handlers_super_admin.router)
    dp.include_router(handlers_admin_settings.router)
    dp.include_router(handlers_start.router)
    dp.include_router(handlers_booking.router)
    dp.include_router(handlers_customer.router)
    dp.include_router(handlers_owner.router)

    reminders_enabled = os.getenv("REMINDER_LOOP_ENABLED", "1").lower() not in {"0", "false", "no"}
    reminder_task = asyncio.create_task(run_reminder_loop()) if reminders_enabled else None

    logger.info("Bot is starting...")
    try:
        await dp.start_polling(bot)
    except Exception as exc:
        logger.error("Polling error: %s", exc)
        raise
    finally:
        if reminder_task:
            reminder_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
