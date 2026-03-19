import logging

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)


class GlobalErrorHandler(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc):
                logger.debug("Ignoring harmless no-op edit: %s", exc)
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer()
                    except Exception:
                        pass
                return None
            raise
        except Exception as exc:
            logger.exception("Unhandled error: %s", exc)

            user_msg = "⚠️ Tizimda xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."
            if isinstance(event, Message):
                await event.answer(user_msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(user_msg, show_alert=True)
            return None
