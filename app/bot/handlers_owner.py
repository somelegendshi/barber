import os
from datetime import time, timedelta
from typing import Optional

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.bot.keyboards import admin_barbers_keyboard, admin_quick_block_keyboard, main_menu_keyboard
from app.db.repository import (
    block_time_range,
    get_admin_shop_id,
    get_barber,
    get_shop,
    list_all_future_bookings,
    list_barbers,
    list_bookings_detailed,
    list_services,
)
from app.utils.time import combine_date_time, get_now, get_today, to_local

router = Router()


def is_super_admin(user_id: int) -> bool:
    owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    return str(user_id) in [oid.strip() for oid in owner_ids if oid.strip()]


def is_owner(user_id: int) -> bool:
    return is_super_admin(user_id) or get_admin_shop_id(user_id) is not None


async def _notify_access_denied(event):
    text = "Sizda bu bo'limga kirish huquqi yo'q." if getattr(event.from_user, "language_code", "") != "ru" else "У вас нет доступа к этому разделу."
    if isinstance(event, types.CallbackQuery):
        await event.answer(text, show_alert=True)
    else:
        await event.answer(text)


async def _notify_shop_selection_required(event):
    text = (
        "Avval /boss orqali do'kon tanlang yoki shop havolasidan kiring."
        if getattr(event.from_user, "language_code", "") != "ru"
        else
        "Сначала выберите салон через /boss или откройте ссылку салона."
    )
    if isinstance(event, types.CallbackQuery):
        await event.answer(text, show_alert=True)
    else:
        await event.answer(text)


async def get_user_shop_id(user_id: int, state: Optional[FSMContext] = None) -> Optional[int]:
    db_shop_id = get_admin_shop_id(user_id)
    if db_shop_id:
        return db_shop_id
    if is_super_admin(user_id) and state is not None:
        data = await state.get_data()
        return data.get("active_shop_id")
    return None


async def require_owner_shop(event, state: Optional[FSMContext] = None) -> Optional[int]:
    if not is_owner(event.from_user.id):
        await _notify_access_denied(event)
        return None

    shop_id = await get_user_shop_id(event.from_user.id, state)
    if not shop_id:
        await _notify_shop_selection_required(event)
        return None
    return shop_id


@router.message(Command("status"))
async def cmd_system_health(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    shop = get_shop(shop_id)
    if not shop:
        await message.answer("Do'kon topilmadi." if lang == "uz" else "Салон не найден.")
        return

    report = (
        f"<b>Tizim holati</b>\n\nDo'kon: <b>{shop['name']}</b>\nUstalar: {len(list_barbers(shop_id))}\nXizmatlar: {len(list_services(shop_id))}\nKelgusi buyurtmalar: {len(list_all_future_bookings(shop_id))}\n\nTizim ishlamoqda."
        if lang == "uz"
        else
        f"<b>Состояние системы</b>\n\nСалон: <b>{shop['name']}</b>\nМастера: {len(list_barbers(shop_id))}\nУслуги: {len(list_services(shop_id))}\nБудущие записи: {len(list_all_future_bookings(shop_id))}\n\nСистема работает."
    )
    await message.answer(report, parse_mode="HTML")


@router.message(F.text == "📆 Bugun")
@router.message(F.text == "📆 Сегодня")
@router.message(F.text == "Bugun")
@router.message(F.text == "Сегодня")
@router.message(Command("today"))
async def cmd_today(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    shop = get_shop(shop_id)
    timezone_name = shop["timezone"] if shop else "Asia/Tashkent"
    bookings = list_bookings_detailed(shop_id, get_today(timezone_name), timezone_name)

    if not bookings:
        await message.answer("Bugun uchun buyurtma yo'q." if lang == "uz" else "На сегодня записей нет.")
        return

    rows = ["<b>Bugungi buyurtmalar</b>" if lang == "uz" else "<b>Записи на сегодня</b>"]
    for booking in bookings:
        time_text = to_local(booking["start_at"], timezone_name).strftime("%H:%M")
        phone = booking.get("customer_phone") or booking.get("customer_username") or "-"
        rows.append(f"{time_text} • {booking['barber_name']} • {booking['customer_name']} ({phone})")
    await message.answer("\n".join(rows), parse_mode="HTML")


@router.message(F.text == "🗓️ Ertaga")
@router.message(F.text == "🗓️ Завтра")
@router.message(F.text == "Ertaga")
@router.message(F.text == "Завтра")
@router.message(Command("tomorrow"))
async def cmd_tomorrow(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    shop = get_shop(shop_id)
    timezone_name = shop["timezone"] if shop else "Asia/Tashkent"
    bookings = list_bookings_detailed(shop_id, get_today(timezone_name) + timedelta(days=1), timezone_name)

    if not bookings:
        await message.answer("Ertaga uchun buyurtma yo'q." if lang == "uz" else "На завтра записей нет.")
        return

    rows = ["<b>Ertangi buyurtmalar</b>" if lang == "uz" else "<b>Записи на завтра</b>"]
    for booking in bookings:
        time_text = to_local(booking["start_at"], timezone_name).strftime("%H:%M")
        phone = booking.get("customer_phone") or booking.get("customer_username") or "-"
        rows.append(f"{time_text} • {booking['barber_name']} • {booking['customer_name']} ({phone})")
    await message.answer("\n".join(rows), parse_mode="HTML")


@router.message(F.text == "📋 Barcha buyurtmalar")
@router.message(F.text == "📋 Все заказы")
@router.message(F.text == "Barcha buyurtmalar")
@router.message(F.text == "Все заказы")
@router.message(Command("all"))
async def cmd_all(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    shop = get_shop(shop_id)
    timezone_name = shop["timezone"] if shop else "Asia/Tashkent"
    bookings = list_all_future_bookings(shop_id, get_now(timezone_name))

    if not bookings:
        await message.answer("Hozircha buyurtmalar yo'q." if lang == "uz" else "Пока записей нет.")
        return

    rows = ["<b>Barcha buyurtmalar</b>" if lang == "uz" else "<b>Все заказы</b>"]
    current_date = None
    for booking in bookings:
        local_dt = to_local(booking["start_at"], timezone_name)
        date_text = local_dt.strftime("%d.%m.%Y")
        if date_text != current_date:
            rows.append(f"\n<b>{date_text}</b>")
            current_date = date_text
        rows.append(f"{local_dt.strftime('%H:%M')} • {booking['barber_name']} • {booking['customer_name']} • #{booking['id']}")
    await message.answer("\n".join(rows), parse_mode="HTML")


@router.message(F.text == "👤 Mijoz rejimi")
@router.message(F.text == "👤 Режим клиента")
@router.message(F.text == "Mijoz rejimi")
@router.message(F.text == "Режим клиента")
async def switch_to_client_mode(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("lang", "uz")
    await state.update_data(is_admin=False)
    await message.answer("Mijoz rejimiga o'tildi." if lang == "uz" else "Включён режим клиента.", reply_markup=main_menu_keyboard(lang=lang))


@router.message(F.text == "⛔ Vaqtni bloklash")
@router.message(F.text == "⛔ Блокировка времени")
@router.message(F.text == "Vaqtni bloklash")
@router.message(F.text == "Блокировка времени")
@router.message(Command("block"))
async def cmd_block_time(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    barbers = list_barbers(shop_id)
    if not barbers:
        await message.answer("Faol usta topilmadi." if lang == "uz" else "Активные мастера не найдены.")
        return

    await message.answer(
        "Qaysi usta uchun vaqtni bloklaymiz?" if lang == "uz" else "Для какого мастера блокируем время?",
        reply_markup=admin_barbers_keyboard(barbers, prefix="block_barber", lang=lang, back_callback="close_admin_settings"),
    )


@router.callback_query(F.data.startswith("block_barber_"))
async def select_barber_for_block(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    barber_id = int(call.data.split("_")[2])
    lang = (await state.get_data()).get("lang", "uz")
    barber = get_barber(barber_id, shop_id)
    if not barber:
        await call.answer("Usta topilmadi." if lang == "uz" else "Мастер не найден.", show_alert=True)
        return

    text = (
        f"<b>{barber['display_name']}</b> uchun blok vaqtini tanlang:"
        if lang == "uz"
        else
        f"Выберите блок для <b>{barber['display_name']}</b>:"
    )
    await call.message.edit_text(text, reply_markup=admin_quick_block_keyboard(barber_id, lang=lang), parse_mode="HTML")


@router.callback_query(F.data.startswith("block_lunch_"))
async def cb_block_lunch(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    barber_id = int(call.data.split("_")[2])
    barber = get_barber(barber_id, shop_id)
    if not barber:
        await call.answer("Usta topilmadi.", show_alert=True)
        return

    shop = get_shop(shop_id)
    timezone_name = shop["timezone"] if shop else "Asia/Tashkent"
    today = get_today(timezone_name)
    start_at = combine_date_time(today, time(hour=13, minute=0), timezone_name)
    end_at = combine_date_time(today, time(hour=14, minute=0), timezone_name)
    block_time_range(barber_id, start_at, end_at, "Lunch break")

    lang = (await state.get_data()).get("lang", "uz")
    text = (
        f"<b>{barber['display_name']}</b> uchun 13:00-14:00 bloklandi."
        if lang == "uz"
        else
        f"Для <b>{barber['display_name']}</b> заблокировано 13:00-14:00."
    )
    await call.message.edit_text(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("block_1h_"))
async def cb_block_1h(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    barber_id = int(call.data.split("_")[2])
    barber = get_barber(barber_id, shop_id)
    if not barber:
        await call.answer("Usta topilmadi.", show_alert=True)
        return

    shop = get_shop(shop_id)
    timezone_name = shop["timezone"] if shop else "Asia/Tashkent"
    now = get_now(timezone_name)
    end_at = now + timedelta(hours=1)
    block_time_range(barber_id, now, end_at, "Temporary closure")

    lang = (await state.get_data()).get("lang", "uz")
    text = (
        f"<b>{barber['display_name']}</b> uchun {to_local(end_at, timezone_name).strftime('%H:%M')} gacha bloklandi."
        if lang == "uz"
        else
        f"Для <b>{barber['display_name']}</b> время закрыто до {to_local(end_at, timezone_name).strftime('%H:%M')}."
    )
    await call.message.edit_text(text, parse_mode="HTML")
