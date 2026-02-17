from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import logging

logger = logging.getLogger(__name__)

class GlobalErrorHandler(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception(f"Unhandled error: {e}")
            
            # Send friendly message to user
            user_msg = "⚠️ Tizimda xatolik yuz berdi. Iltimos, birozdan so'ng urinib ko'ring."
            
            if isinstance(event, Message):
                await event.answer(user_msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(user_msg, show_alert=True)
            return
