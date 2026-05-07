import logging

from app.db.repository import list_booking_notification_ids
from app.utils.time import to_local

logger = logging.getLogger(__name__)


def _format_booking_time(start_at, timezone_name: str) -> str:
    return to_local(start_at, timezone_name).strftime("%d.%m %H:%M")


def _booking_message(
    *,
    title: str,
    booking_id: int,
    shop_name: str,
    barber_name: str,
    service_name: str,
    customer_name: str,
    customer_phone: str | None,
    time_text: str,
) -> str:
    return (
        f"<b>{title}</b>\n\n"
        f"ID: <code>{booking_id}</code>\n"
        f"Shop / Salon: {shop_name}\n"
        f"Customer / Client: {customer_name}\n"
        f"Phone: {customer_phone or '-'}\n"
        f"Barber / Master: {barber_name}\n"
        f"Service: {service_name}\n"
        f"Time: {time_text}"
    )


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
    customer_phone: str | None,
    start_at,
):
    recipient_ids = list_booking_notification_ids(shop_id, barber_id)
    if not recipient_ids:
        return

    message = _booking_message(
        title="New booking / Novaya zapis'",
        booking_id=booking_id,
        shop_name=shop_name,
        barber_name=barber_name,
        service_name=service_name,
        customer_name=customer_name,
        customer_phone=customer_phone,
        time_text=_format_booking_time(start_at, timezone_name),
    )
    for recipient_id in recipient_ids:
        try:
            await bot.send_message(chat_id=recipient_id, text=message, parse_mode="HTML")
        except Exception as exc:
            logger.warning("Failed to send new-booking notification to %s: %s", recipient_id, exc)


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
    customer_phone: str | None,
    start_at,
):
    recipient_ids = list_booking_notification_ids(shop_id, barber_id)
    if not recipient_ids:
        return

    message = _booking_message(
        title="Booking cancelled / Zapis' otmenena",
        booking_id=booking_id,
        shop_name=shop_name,
        barber_name=barber_name,
        service_name=service_name,
        customer_name=customer_name,
        customer_phone=customer_phone,
        time_text=_format_booking_time(start_at, timezone_name),
    )
    for recipient_id in recipient_ids:
        try:
            await bot.send_message(chat_id=recipient_id, text=message, parse_mode="HTML")
        except Exception as exc:
            logger.warning("Failed to send cancellation notification to %s: %s", recipient_id, exc)
