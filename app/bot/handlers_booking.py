from datetime import datetime, timedelta

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.bot.keyboards import (
    barbers_keyboard,
    confirm_keyboard,
    dates_keyboard,
    main_menu_keyboard,
    phone_confirm_keyboard,
    phone_keyboard,
    services_keyboard,
    slots_keyboard,
)
from app.bot.messages import get_msg
from app.bot.notifications import send_new_booking_notifications
from app.db.repository import (
    ensure_customer,
    get_barber,
    get_bookings,
    get_customer_phone,
    get_service,
    get_shop,
    get_time_off,
    get_work_hours,
    insert_booking,
    list_barbers,
    list_services,
)
from app.domain.slotting import generate_slots
from app.utils.text import normalize_phone
from app.utils.time import combine_date_time, format_date_localized, get_now, get_today, to_local

router = Router()


def _available_slot_labels(
    *,
    shop_id: int,
    barber_id: int,
    selected_date,
    service_duration_min: int,
    timezone_name: str,
):
    work_hours = get_work_hours(barber_id)
    start_dt = combine_date_time(selected_date, datetime.min.time(), timezone_name)
    end_dt = combine_date_time(selected_date, datetime.max.time(), timezone_name)

    bookings = get_bookings(shop_id=shop_id, barber_id=barber_id, start_dt=start_dt, end_dt=end_dt)
    time_off = get_time_off(barber_id, start_dt, end_dt)

    naive_bookings = [
        {
            "start_at": to_local(booking["start_at"], timezone_name).replace(tzinfo=None),
            "end_at": to_local(booking["end_at"], timezone_name).replace(tzinfo=None),
        }
        for booking in bookings
    ]
    naive_time_off = [
        {
            "start_at": to_local(block["start_at"], timezone_name).replace(tzinfo=None),
            "end_at": to_local(block["end_at"], timezone_name).replace(tzinfo=None),
        }
        for block in time_off
    ]

    slot_datetimes = generate_slots(
        work_hours,
        naive_bookings,
        naive_time_off,
        service_duration_min,
        selected_date,
        not_before=get_now(timezone_name).replace(tzinfo=None),
    )
    return [slot.strftime("%H:%M") for slot in slot_datetimes]


class BookingFlow(StatesGroup):
    SERVICE = State()
    BARBER = State()
    DATE = State()
    TIME = State()
    PHONE = State()
    CONFIRM = State()


async def _return_to_menu(target_message, lang: str):
    await target_message.answer(
        "Asosiy menyu" if lang == "uz" else "Главное меню",
        reply_markup=main_menu_keyboard(lang=lang),
    )


async def _reset_flow_state(state: FSMContext):
    data = await state.get_data()
    preserved = {
        key: value
        for key, value in data.items()
        if key in {"active_shop_id", "lang", "is_admin"}
    }
    await state.clear()
    if preserved:
        await state.update_data(**preserved)


@router.callback_query(F.data == "cancel_flow")
async def cancel_flow_handler(call: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("lang", "uz")
    await _reset_flow_state(state)
    await call.message.delete()
    await _return_to_menu(call.message, lang)


@router.callback_query(F.data == "cancel_booking")
async def cancel_booking_handler(call: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("lang", "uz")
    await _reset_flow_state(state)
    await call.message.edit_text("Bekor qilindi." if lang == "uz" else "Отменено.")
    await _return_to_menu(call.message, lang)


@router.callback_query(F.data == "back_to_services")
async def back_to_services(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id")
    if not shop_id:
        await call.answer("Session tugagan." if lang == "uz" else "Сессия завершена.", show_alert=True)
        return

    services = list_services(shop_id=shop_id)
    await call.message.edit_text(
        get_msg("select_service", lang=lang),
        reply_markup=services_keyboard(services, lang=lang),
        parse_mode="HTML",
    )
    await state.set_state(BookingFlow.SERVICE)


@router.callback_query(F.data == "back_to_barbers")
async def back_to_barbers(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id")
    if not shop_id:
        await call.answer("Session tugagan." if lang == "uz" else "Сессия завершена.", show_alert=True)
        return

    barbers = list_barbers(shop_id=shop_id)
    await call.message.edit_text(
        get_msg("select_barber", lang=lang),
        reply_markup=barbers_keyboard(barbers, lang=lang),
        parse_mode="HTML",
    )
    await state.set_state(BookingFlow.BARBER)


@router.callback_query(F.data == "back_to_dates")
async def back_to_dates(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id")
    if not shop_id or "barber_id" not in data:
        await call.answer("Session tugagan." if lang == "uz" else "Сессия завершена.", show_alert=True)
        return

    shop = get_shop(shop_id)
    timezone_name = shop["timezone"] if shop else "Asia/Tashkent"
    today = get_today(timezone_name)
    dates = [
        {
            "text": format_date_localized(today + timedelta(days=index), lang),
            "callback": f"date_{(today + timedelta(days=index)).strftime('%Y-%m-%d')}",
        }
        for index in range(7)
    ]
    await call.message.edit_text(
        get_msg("select_date", lang=lang),
        reply_markup=dates_keyboard(dates, lang=lang),
        parse_mode="HTML",
    )
    await state.set_state(BookingFlow.DATE)


@router.callback_query(F.data.startswith("service_"))
async def select_barber(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    shop_id = data.get("active_shop_id")
    lang = data.get("lang", "uz")
    if not shop_id:
        await call.answer("Session tugagan." if lang == "uz" else "Сессия завершена.", show_alert=True)
        return

    service_id = int(call.data.split("_")[1])
    service = get_service(service_id, shop_id)
    if not service:
        await call.answer("Xizmat topilmadi." if lang == "uz" else "Услуга не найдена.", show_alert=True)
        return

    await state.update_data(
        service_id=service_id,
        duration=service["duration_min"],
        service_name=service["name"],
    )
    barbers = list_barbers(shop_id=shop_id)
    await call.message.edit_text(
        get_msg("select_barber", lang=lang),
        reply_markup=barbers_keyboard(barbers, lang=lang),
        parse_mode="HTML",
    )
    await state.set_state(BookingFlow.BARBER)


@router.callback_query(F.data.startswith("barber_"))
async def select_date(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    shop_id = data.get("active_shop_id")
    lang = data.get("lang", "uz")
    if not shop_id:
        await call.answer("Session tugagan." if lang == "uz" else "Сессия завершена.", show_alert=True)
        return

    barber_id = int(call.data.split("_")[1])
    barber = get_barber(barber_id, shop_id)
    if not barber:
        await call.answer("Usta topilmadi." if lang == "uz" else "Мастер не найден.", show_alert=True)
        return

    shop = get_shop(shop_id)
    timezone_name = shop["timezone"] if shop else "Asia/Tashkent"
    today = get_today(timezone_name)
    dates = [
        {
            "text": format_date_localized(today + timedelta(days=index), lang),
            "callback": f"date_{(today + timedelta(days=index)).strftime('%Y-%m-%d')}",
        }
        for index in range(7)
    ]

    await state.update_data(barber_id=barber_id, barber_name=barber["display_name"])
    await call.message.edit_text(
        get_msg("select_date", lang=lang),
        reply_markup=dates_keyboard(dates, lang=lang),
        parse_mode="HTML",
    )
    await state.set_state(BookingFlow.DATE)


@router.callback_query(F.data.startswith("date_"))
async def select_time(call: types.CallbackQuery, state: FSMContext):
    selected_date_str = call.data.split("_")[1]
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    await state.update_data(date=selected_date_str)

    data = await state.get_data()
    shop_id = data.get("active_shop_id")
    barber_id = data.get("barber_id")
    lang = data.get("lang", "uz")
    if not shop_id or not barber_id:
        await call.answer("Session tugagan." if lang == "uz" else "Сессия завершена.", show_alert=True)
        return

    shop = get_shop(shop_id)
    barber = get_barber(barber_id, shop_id)
    if not shop or not barber:
        await call.answer(
            "Shop yoki usta topilmadi."
            if lang == "uz"
            else
            "Салон или мастер не найден.",
            show_alert=True,
        )
        return

    timezone_name = shop["timezone"]
    slot_labels = _available_slot_labels(
        shop_id=shop_id,
        barber_id=barber_id,
        selected_date=selected_date,
        service_duration_min=int(data.get("duration", 30)),
        timezone_name=timezone_name,
    )

    if not slot_labels:
        await call.answer(
            "Bu kunda bo'sh vaqt qolmagan."
            if lang == "uz"
            else
            "На этот день свободного времени нет.",
            show_alert=True,
        )
        return

    await call.message.edit_text(
        get_msg("select_time", lang=lang),
        reply_markup=slots_keyboard(slot_labels, lang=lang),
        parse_mode="HTML",
    )
    await state.set_state(BookingFlow.TIME)


@router.callback_query(F.data.startswith("time_"))
async def check_phone_step(call: types.CallbackQuery, state: FSMContext):
    payload = call.data[5:]
    if "_" in payload:
        date_str, time_str = payload.split("_", 1)
        await state.update_data(date=date_str, time=time_str)
    else:
        await state.update_data(time=payload)

    data = await state.get_data()
    lang = data.get("lang", "uz")

    stored_phone = get_customer_phone(call.from_user.id)
    if stored_phone:
        text = (
            f"{stored_phone}\nShu raqamni ishlatamizmi?"
            if lang == "uz"
            else
            f"{stored_phone}\nИспользуем этот номер?"
        )
        await state.update_data(phone=stored_phone)
        await call.message.edit_text(text, reply_markup=phone_confirm_keyboard(lang=lang))
        return

    await call.message.delete()
    await call.message.answer(
        get_msg("request_phone", lang=lang),
        reply_markup=phone_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await state.set_state(BookingFlow.PHONE)


@router.callback_query(F.data == "use_existing_phone")
async def use_existing_phone_handler(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await show_confirmation(call.message, state, data.get("phone"), user=call.from_user)


@router.callback_query(F.data == "change_phone")
async def change_phone_handler(call: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("lang", "uz")
    await call.message.delete()
    await call.message.answer(
        get_msg("request_phone", lang=lang),
        reply_markup=phone_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await state.set_state(BookingFlow.PHONE)


@router.message(BookingFlow.PHONE, F.contact)
async def receive_contact(message: types.Message, state: FSMContext):
    await process_phone_input(
        message,
        state,
        normalize_phone(message.contact.phone_number) or message.contact.phone_number,
    )


@router.message(BookingFlow.PHONE)
async def receive_phone_text(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("lang", "uz")
    phone = normalize_phone((message.text or "").strip())
    if not phone:
        await message.answer(
            "To'g'ri raqam kiriting."
            if lang == "uz"
            else
            "Введите корректный номер."
        )
        return
    await process_phone_input(message, state, phone)


async def process_phone_input(message: types.Message, state: FSMContext, phone: str):
    lang = (await state.get_data()).get("lang", "uz")
    customer_id = ensure_customer(
        message.from_user.id,
        message.from_user.full_name,
        phone,
        message.from_user.username,
        language_code=lang,
    )
    await state.update_data(phone=phone, customer_id=customer_id)
    await message.answer(
        "✅ Raqam saqlandi." if lang == "uz" else "✅ Номер сохранён.",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await show_confirmation(message, state, phone, user=message.from_user)


async def show_confirmation(message: types.Message, state: FSMContext, phone: str, user: types.User):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    if "customer_id" not in data:
        customer_id = ensure_customer(
            user.id,
            user.full_name,
            phone,
            user.username,
            language_code=lang,
        )
        await state.update_data(customer_id=customer_id)

    date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()
    formatted_date = format_date_localized(date_obj, lang)
    text = get_msg(
        "confirm",
        lang=lang,
        barber=data.get("barber_name", "-"),
        service=data["service_name"],
        date=formatted_date,
        time=data["time"],
        phone=phone,
    )
    await message.answer(text, reply_markup=confirm_keyboard(lang=lang), parse_mode="HTML")
    await state.set_state(BookingFlow.CONFIRM)


@router.callback_query(F.data == "confirm_booking")
async def finalize_booking(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id")
    required_fields = {"service_id", "barber_id", "customer_id", "date", "time"}
    if not shop_id or not required_fields.issubset(data):
        await call.answer("Session tugagan." if lang == "uz" else "Session expired.", show_alert=True)
        await _reset_flow_state(state)
        return

    shop = get_shop(shop_id)
    service = get_service(data.get("service_id"), shop_id)
    barber = get_barber(data.get("barber_id"), shop_id)
    if not shop or not service or not barber:
        await call.message.edit_text(
            "Buyurtmani yakunlab bo'lmadi. Qaytadan urinib ko'ring."
            if lang == "uz"
            else
            "Не удалось завершить запись. Попробуйте снова."
        )
        await _reset_flow_state(state)
        return

    timezone_name = shop["timezone"]
    try:
        booking_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        booking_time = datetime.strptime(data["time"], "%H:%M").time()
    except ValueError:
        await call.answer("Session tugagan." if lang == "uz" else "Session expired.", show_alert=True)
        await _reset_flow_state(state)
        return
    start_at = combine_date_time(booking_date, booking_time, timezone_name)
    duration = int(service["duration_min"])

    available_slots = _available_slot_labels(
        shop_id=shop_id,
        barber_id=barber["id"],
        selected_date=booking_date,
        service_duration_min=duration,
        timezone_name=timezone_name,
    )
    if data["time"] not in available_slots:
        await call.message.edit_text(get_msg("error_unavailable", lang=lang), parse_mode="HTML")
        await _return_to_menu(call.message, lang)
        await _reset_flow_state(state)
        return

    booking_id = insert_booking(
        {
            "shop_id": shop_id,
            "barber_id": barber["id"],
            "service_id": service["id"],
            "customer_id": data["customer_id"],
            "customer_name": call.from_user.full_name,
            "start_at": start_at,
            "end_at": start_at + timedelta(minutes=duration),
        }
    )

    if booking_id:
        await call.message.edit_text(get_msg("success", lang=lang, id=booking_id), parse_mode="HTML")
        await _return_to_menu(call.message, lang)
        await send_new_booking_notifications(
            bot,
            booking_id=booking_id,
            shop_id=shop_id,
            shop_name=shop["name"],
            timezone_name=timezone_name,
            barber_id=barber["id"],
            barber_name=barber["display_name"],
            service_name=service["name"],
            customer_name=call.from_user.full_name,
            customer_phone=data.get("phone"),
            start_at=start_at,
        )
    else:
        await call.message.edit_text(get_msg("error_taken", lang=lang), parse_mode="HTML")
        await _return_to_menu(call.message, lang)

    await _reset_flow_state(state)
