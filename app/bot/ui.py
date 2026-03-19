from aiogram.exceptions import TelegramBadRequest


async def safe_edit_text(message, text: str, callback=None, **kwargs):
    try:
        return await message.edit_text(text, **kwargs)
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise
        if callback is not None:
            try:
                await callback.answer()
            except Exception:
                return None
        return None
