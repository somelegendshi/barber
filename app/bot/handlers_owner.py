import os
from datetime import datetime, time, timedelta
from typing import Optional

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.bot.keyboards import admin_barbers_keyboard, admin_quick_block_keyboard, main_menu_keyboard
from app.db.repository import (
    block_time_range,
    get_admin_shop_id,
    get_barber,
    get_shop,
    list_all_future_bookings,
    list_barbers,
    list_bookings_detailed,
    list_confirmed_bookings_from,
    list_services,
)
from app.utils.time import combine_date_time, get_now, get_today, to_local

router = Router()
MAX_MESSAGE_LEN = 3800


class BlockTimeStates(StatesGroup):
    CUSTOM_RANGE = State()


def is_super_admin(user_id: int) -> bool:
    owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    return str(user_id) in [oid.strip() for oid in owner_ids if oid.strip()]


def is_owner(user_id: int) -> bool:
    return is_super_admin(user_id) or get_admin_shop_id(user_id) is not None


def _all_bookings_start_dt(timezone_name: str):
    return combine_date_time(get_today(timezone_name), time.min, timezone_name)


def _chunk_message_lines(lines, max_len: int = MAX_MESSAGE_LEN):
    chunks = []
    current_lines = []
    current_len = 0

    for line in lines:
        line_len = len(line) + (1 if current_lines else 0)
        if current_lines and current_len + line_len > max_len:
            chunks.append("\n".join(current_lines))
            current_lines = [line]
            current_len = len(line)
            continue

        current_lines.append(line)
        current_len += line_len

    if current_lines:
        chunks.append("\n".join(current_lines))
    return chunks


async def _send_booking_lines(message: types.Message, lines):
    for chunk in _chunk_message_lines(lines):
        await message.answer(chunk, parse_mode="HTML")


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


async def _reset_owner_state(state: FSMContext):
    data = await state.get_data()
    preserved = {
        key: value
        for key, value in data.items()
        if key in {"active_shop_id", "lang", "is_admin"}
    }
    await state.clear()
    if preserved:
        await state.update_data(**preserved)


def _parse_custom_block_input(text: str, timezone_name: str, now_dt=None):
    value = (text or "").strip()
    if not value:
        raise ValueError("Format: 2026-05-07 or 2026-05-07 14:00-16:30")

    try:
        if " " not in value:
            day = datetime.strptime(value, "%Y-%m-%d").date()
            start_at = combine_date_time(day, time.min, timezone_name)
            end_at = combine_date_time(day + timedelta(days=1), time.min, timezone_name)
        else:
            date_text, range_text = value.split(maxsplit=1)
            start_text, end_text = [part.strip() for part in range_text.split("-", 1)]
            day = datetime.strptime(date_text, "%Y-%m-%d").date()
            start_clock = datetime.strptime(start_text, "%H:%M").time()
            end_clock = datetime.strptime(end_text, "%H:%M").time()
            start_at = combine_date_time(day, start_clock, timezone_name)
            end_at = combine_date_time(day, end_clock, timezone_name)
    except ValueError as exc:
        raise ValueError("Format: 2026-05-07 or 2026-05-07 14:00-16:30") from exc

    if end_at <= start_at:
        raise ValueError("Tugash vaqti boshlanishdan keyin bo'lishi kerak.")

    now_dt = now_dt or get_now(timezone_name)
    if end_at <= now_dt:
        raise ValueError("Blok vaqti kelajakda bo'lishi kerak.")

    return start_at, end_at


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
    await _send_booking_lines(message, rows)


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
    await _send_booking_lines(message, rows)


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
    bookings = list_confirmed_bookings_from(shop_id, _all_bookings_start_dt(timezone_name))

    if not bookings:
        await message.answer("Hozircha buyurtmalar yo'q." if lang == "uz" else "Пока записей нет.")
        return

    rows = ["<b>Barcha buyurtmalar</b>" if lang == "uz" else "<b>Все заказы</b>"]
    current_date = None
    for booking in bookings:
        local_dt = to_local(booking["start_at"], timezone_name)
        date_text = local_dt.strftime("%d.%m.%Y")
        if date_text != current_date:
            if current_date is not None:
                rows.append("")
            rows.append(f"<b>{date_text}</b>")
            current_date = date_text
        rows.append(f"{local_dt.strftime('%H:%M')} • {booking['barber_name']} • {booking['customer_name']} • #{booking['id']}")
    await _send_booking_lines(message, rows)


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

    await state.update_data(block_barber_id=barber_id)
    text = (
        f"<b>{barber['display_name']}</b> uchun blok vaqtini tanlang:"
        if lang == "uz"
        else
        f"Выберите блок для <b>{barber['display_name']}</b>:"
    )
    await call.message.edit_text(text, reply_markup=admin_quick_block_keyboard(barber_id, lang=lang), parse_mode="HTML")


@router.callback_query(F.data.startswith("block_custom_"))
async def custom_block_start(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    barber_id = int(call.data.split("_")[2])
    lang = (await state.get_data()).get("lang", "uz")
    barber = get_barber(barber_id, shop_id)
    if not barber:
        await call.answer("Usta topilmadi." if lang == "uz" else "Мастер не найден.", show_alert=True)
        return

    await state.update_data(block_barber_id=barber_id)
    text = (
        "Blok qilinadigan sanani yoki vaqt oralig'ini yuboring:\n\n"
        "<code>2026-05-07</code>\n"
        "<code>2026-05-07 14:00-16:30</code>"
        if lang == "uz"
        else
        "Отправьте дату или интервал для блокировки:\n\n"
        "<code>2026-05-07</code>\n"
        "<code>2026-05-07 14:00-16:30</code>"
    )
    await call.message.answer(text, parse_mode="HTML")
    await state.set_state(BlockTimeStates.CUSTOM_RANGE)
    await call.answer()


@router.message(BlockTimeStates.CUSTOM_RANGE)
async def custom_block_finish(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")
    barber_id = data.get("block_barber_id")
    if not barber_id:
        await _reset_owner_state(state)
        await message.answer("Session tugadi." if lang == "uz" else "Сессия завершена.")
        return

    barber = get_barber(barber_id, shop_id)
    shop = get_shop(shop_id)
    if not barber or not shop:
        await _reset_owner_state(state)
        await message.answer("Usta yoki do'kon topilmadi." if lang == "uz" else "Мастер или салон не найден.")
        return

    timezone_name = shop["timezone"]
    try:
        start_at, end_at = _parse_custom_block_input(message.text or "", timezone_name)
    except ValueError as exc:
        await message.answer(str(exc))
        return

    block_time_range(barber_id, start_at, end_at, "Manual custom block")
    await _reset_owner_state(state)

    start_text = to_local(start_at, timezone_name).strftime("%d.%m.%Y %H:%M")
    end_text = to_local(end_at, timezone_name).strftime("%d.%m.%Y %H:%M")
    await message.answer(
        f"<b>{barber['display_name']}</b> uchun bloklandi:\n{start_text} - {end_text}"
        if lang == "uz"
        else
        f"Для <b>{barber['display_name']}</b> заблокировано:\n{start_text} - {end_text}",
        parse_mode="HTML",
    )


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
