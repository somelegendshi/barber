import logging

from app.db.repository import list_booking_notification_ids
from app.utils.time import to_local

logger = logging.getLogger(__name__)


def _format_booking_time(start_at, timezone_name: str) -> str:
    return to_local(start_at, timezone_name).strftime("%d.%m %H:%M")


async def send_new_booking_notifications(
    bot,
    *,
    booking_id: int,
    shop_id: int,
    shop_name: str,
    timezone_name: str,
    barber_id: int,
    barber_name: str,
    service_name: str,
    customer_name: str,
    start_at,
):
    recipient_ids = list_booking_notification_ids(shop_id, barber_id)
    if not recipient_ids:
        return

    time_text = _format_booking_time(start_at, timezone_name)
    message = (
        "<b>🔔 Yangi buyurtma / 🔔 Новая запись</b>\n\n"
        f"🆔 ID: <code>{booking_id}</code>\n"
        f"🏪 Do'kon / Салон: {shop_name}\n"
        f"👤 Mijoz / Клиент: {customer_name}\n"
        f"💈 Usta / Мастер: {barber_name}\n"
        f"✂️ Xizmat / Услуга: {service_name}\n"
        f"🕒 Vaqt / Время: {time_text}"
    )
    for recipient_id in recipient_ids:
        try:
            await bot.send_message(chat_id=recipient_id, text=message, parse_mode="HTML")
        except Exception as exc:
            logger.warning("Failed to send new-booking notification to %s: %s", recipient_id, exc)
            continue


async def send_booking_cancelled_notifications(
    bot,
    *,
    booking_id: int,
    shop_id: int,
    shop_name: str,
    timezone_name: str,
    barber_id: int,
    barber_name: str,
    service_name: str,
    customer_name: str,
    start_at,
):
    recipient_ids = list_booking_notification_ids(shop_id, barber_id)
    if not recipient_ids:
        return

    time_text = _format_booking_time(start_at, timezone_name)
    message = (
        "<b>❌ Buyurtma bekor qilindi / ❌ Запись отменена</b>\n\n"
        f"🆔 ID: <code>{booking_id}</code>\n"
        f"🏪 Do'kon / Салон: {shop_name}\n"
        f"👤 Mijoz / Клиент: {customer_name}\n"
        f"💈 Usta / Мастер: {barber_name}\n"
        f"✂️ Xizmat / Услуга: {service_name}\n"
        f"🕒 Vaqt / Время: {time_text}"
    )
    for recipient_id in recipient_ids:
        try:
            await bot.send_message(chat_id=recipient_id, text=message, parse_mode="HTML")
        except Exception as exc:
            logger.warning("Failed to send cancellation notification to %s: %s", recipient_id, exc)
            continue
