from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.bot.keyboards import my_booking_keyboard
from app.bot.notifications import send_booking_cancelled_notifications
from app.db.repository import (
    cancel_booking_by_customer,
    get_customer_booking_for_notification,
    get_customer_language,
    list_customer_bookings,
)
from app.utils.text import resolve_lang
from app.utils.time import to_local

router = Router()


@router.message(F.text == "📅 Mening buyurtmalarim")
@router.message(F.text == "📅 Мои записи")
@router.message(F.text == "Mening buyurtmalarim")
@router.message(F.text == "Мои записи")
@router.message(Command("my"))
async def cmd_my_bookings(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    lang = resolve_lang(
        data.get("lang"),
        get_customer_language(user_id),
        telegram_lang=message.from_user.language_code,
    )
    await state.update_data(lang=lang)

    bookings = list_customer_bookings(user_id, None)
    if not bookings:
        await message.answer(
            "📭 Sizda faol buyurtmalar yo'q."
            if lang == "uz"
            else
            "📭 У вас нет активных записей."
        )
        return

    await message.answer(
        "📅 <b>Sizning faol buyurtmalaringiz:</b>"
        if lang == "uz"
        else
        "📅 <b>Ваши активные записи:</b>",
        parse_mode="HTML",
    )

    for booking in bookings:
        local_dt = to_local(booking["start_at"], booking.get("shop_timezone"))
        if lang == "uz":
            text = (
                f"✂️ <b>{booking['service_name']}</b>\n"
                f"🏪 Do'kon: {booking['shop_name']}\n"
                f"💈 Usta: {booking['barber_name']}\n"
                f"🕒 Vaqt: {local_dt.strftime('%d.%m %H:%M')}\n"
                f"🆔 ID: <code>{booking['id']}</code>"
            )
        else:
            text = (
                f"✂️ <b>{booking['service_name']}</b>\n"
                f"🏪 Салон: {booking['shop_name']}\n"
                f"💈 Мастер: {booking['barber_name']}\n"
                f"🕒 Время: {local_dt.strftime('%d.%m %H:%M')}\n"
                f"🆔 ID: <code>{booking['id']}</code>"
            )
        await message.answer(
            text,
            reply_markup=my_booking_keyboard(booking["id"], lang=lang),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("cancel_me_"))
async def cancel_my_booking(call: types.CallbackQuery, state: FSMContext):
    booking_id = int(call.data.split("_")[2])
    lang = (await state.get_data()).get("lang", "uz")
    booking = get_customer_booking_for_notification(booking_id, call.from_user.id)

    success = cancel_booking_by_customer(booking_id, call.from_user.id)
    if success:
        await call.message.edit_text(
            f"✅ Buyurtma #{booking_id} bekor qilindi."
            if lang == "uz"
            else
            f"✅ Запись #{booking_id} отменена."
        )
        if booking:
            await send_booking_cancelled_notifications(
                call.bot,
                booking_id=booking_id,
                shop_id=booking["shop_id"],
                shop_name=booking["shop_name"],
                timezone_name=booking["shop_timezone"],
                barber_id=booking["barber_id"],
                barber_name=booking["barber_name"],
                service_name=booking["service_name"],
                customer_name=booking.get("customer_name") or call.from_user.full_name,
                start_at=booking["start_at"],
            )
    else:
        await call.answer(
            "⚠️ Buyurtma topilmadi yoki sizga tegishli emas."
            if lang == "uz"
            else
            "⚠️ Запись не найдена или не принадлежит вам.",
            show_alert=True,
        )


@router.callback_query(F.data.startswith("reschedule_"))
async def reschedule_booking(call: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("lang", "uz")
    await call.answer(
        "🔁 Avval mavjud buyurtmani bekor qiling, keyin yangisini yarating."
        if lang == "uz"
        else
        "🔁 Сначала отмените текущую запись, затем создайте новую.",
        show_alert=True,
    )
