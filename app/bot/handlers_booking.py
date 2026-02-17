from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
import logging
import os
import pytz

from app.db.repository import list_barbers, get_work_hours, get_bookings, insert_booking, get_shop, list_services, get_service, get_customer_phone, ensure_customer, get_shop_owner_id
from app.domain.slotting import generate_slots
from app.bot.keyboards import (
    barbers_keyboard, dates_keyboard, slots_keyboard, confirm_keyboard, 
    phone_keyboard, main_menu_keyboard, services_keyboard, phone_confirm_keyboard
)
from app.bot.messages import get_msg
from app.utils.time import get_today, TZ_TASHKENT, format_date_localized

router = Router()

class BookingFlow(StatesGroup):
    SERVICE = State()
    BARBER = State()
    DATE = State()
    TIME = State()
    PHONE = State()
    CONFIRM = State()

# --- NAVIGATION HANDLERS (BACK) ---

@router.callback_query(F.data == "cancel_flow")
async def cancel_flow_handler(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    
@router.callback_query(F.data == "back_to_services")
async def back_to_services(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id", 1)
    
    services = list_services(shop_id=shop_id)
    msg_text = get_msg("select_service", lang=lang)
    
    await call.message.edit_text(msg_text, reply_markup=services_keyboard(services, lang=lang))
    await state.set_state(BookingFlow.SERVICE)

@router.callback_query(F.data == "back_to_barbers")
async def back_to_barbers(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id", 1)
    
    barbers = list_barbers(shop_id=shop_id)
    msg_text = get_msg("select_barber", lang=lang)
    
    await call.message.edit_text(msg_text, reply_markup=barbers_keyboard(barbers, lang=lang))
    await state.set_state(BookingFlow.BARBER)

# --- SELECTION HANDLERS ---

@router.callback_query(F.data.startswith("service_"))
async def select_barber(call: types.CallbackQuery, state: FSMContext):
    service_id = int(call.data.split("_")[1])
    service = get_service(service_id)
    if not service:
        await call.answer("Error: Service not found", show_alert=True)
        return
        
    await state.update_data(service_id=service_id, duration=service['duration_min'], service_name=service['name'])
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id", 1)
    
    barbers = list_barbers(shop_id=shop_id)
    msg_text = get_msg("select_barber", lang=lang)
    await call.message.edit_text(msg_text, reply_markup=barbers_keyboard(barbers, lang=lang))
    await state.set_state(BookingFlow.BARBER)

@router.callback_query(F.data.startswith("barber_"))
async def select_date(call: types.CallbackQuery, state: FSMContext):
    barber_id = int(call.data.split("_")[1])
    await state.update_data(barber_id=barber_id)
    data = await state.get_data()
    lang = data.get("lang", "uz")
    
    today = get_today()
    dates = [{"text": format_date_localized(today + timedelta(days=i), lang), "callback": f"date_{(today + timedelta(days=i)).strftime('%Y-%m-%d')}"} for i in range(7)]
    
    msg_text = get_msg("select_date", lang=lang)
    await call.message.edit_text(msg_text, reply_markup=dates_keyboard(dates, lang=lang))
    await state.set_state(BookingFlow.DATE)

@router.callback_query(F.data.startswith("date_"))
async def select_time(call: types.CallbackQuery, state: FSMContext):
    selected_date_str = call.data.split("_")[1]
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    await state.update_data(date=selected_date_str)
    
    data = await state.get_data()
    shop_id = data.get("active_shop_id", 1)
    barber_id = data['barber_id']
    lang = data.get("lang", "uz")
    
    work_hours = get_work_hours(barber_id)
    bookings = get_bookings(shop_id=shop_id, barber_id=barber_id, start_dt=datetime.combine(selected_date, datetime.min.time()), end_dt=datetime.combine(selected_date, datetime.max.time()))
    
    naive_bookings = [{'start_at': b['start_at'].astimezone(TZ_TASHKENT).replace(tzinfo=None), 'end_at': b['end_at'].astimezone(TZ_TASHKENT).replace(tzinfo=None)} for b in bookings]
    slots = generate_slots(work_hours, naive_bookings, [], int(data.get('duration', 30)), selected_date)
    slot_strs = [s.strftime("%H:%M") for s in slots]
    
    if not slot_strs:
        await call.answer("Vaqt qolmadi", show_alert=True)
        return

    await call.message.edit_text(get_msg("select_time", lang=lang), reply_markup=slots_keyboard(slot_strs, lang=lang))
    await state.set_state(BookingFlow.TIME)

@router.callback_query(F.data.startswith("time_"))
async def check_phone_step(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(time=call.data.split("_")[1])
    data = await state.get_data()
    lang = data.get("lang", "uz")
    
    stored_phone = get_customer_phone(call.from_user.id)
    if stored_phone:
        msg = f"📱 {stored_phone}\nShu raqamni qoldiramizmi?" if lang=="uz" else f"📱 {stored_phone}\nОставить этот номер?"
        await state.update_data(phone=stored_phone)
        await call.message.edit_text(msg, reply_markup=phone_confirm_keyboard(lang=lang))
    else:
        await call.message.delete()
        await call.message.answer(get_msg("request_phone", lang=lang), reply_markup=phone_keyboard(lang=lang))
        await state.set_state(BookingFlow.PHONE)

@router.callback_query(F.data == "use_existing_phone")
async def use_existing_phone_handler(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await show_confirmation(call.message, state, data.get('phone'), user=call.from_user)

@router.callback_query(F.data == "change_phone")
async def change_phone_handler(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.message.delete()
    await call.message.answer(get_msg("request_phone", lang=data.get("lang", "uz")), reply_markup=phone_keyboard(lang=data.get("lang", "uz")))
    await state.set_state(BookingFlow.PHONE)

@router.message(BookingFlow.PHONE, F.contact)
async def receive_contact(message: types.Message, state: FSMContext):
    await process_phone_input(message, state, message.contact.phone_number)

@router.message(BookingFlow.PHONE)
async def receive_phone_text(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    import re
    if not re.match(r'^\+?[0-9]{7,15}$', phone):
        await message.answer("⚠️ To'g'ri raqam kiriting.")
        return
    await process_phone_input(message, state, phone)

async def process_phone_input(message: types.Message, state: FSMContext, phone: str):
    cid = ensure_customer(message.from_user.id, message.from_user.full_name, phone, message.from_user.username)
    await state.update_data(phone=phone, customer_id=cid)
    await message.answer("🆗", reply_markup=types.ReplyKeyboardRemove())
    await show_confirmation(message, state, phone, user=message.from_user)

async def show_confirmation(message: types.Message, state: FSMContext, phone: str, user: types.User):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    if 'customer_id' not in data:
        cid = ensure_customer(user.id, user.full_name, phone, user.username)
        await state.update_data(customer_id=cid)
    
    msg = get_msg("confirm", lang=lang, barber=f"ID {data['barber_id']}", service=data['service_name'], date=data['date'], time=data['time'], phone=phone)
    await message.answer(msg, reply_markup=confirm_keyboard(lang=lang))
    await state.set_state(BookingFlow.CONFIRM)

@router.callback_query(F.data == "confirm_booking")
async def finalize_booking(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    shop_id = data.get("active_shop_id", 1)
    
    start_at = TZ_TASHKENT.localize(datetime.combine(datetime.strptime(data['date'], "%Y-%m-%d").date(), datetime.strptime(data['time'], "%H:%M").time()))
    
    booking_id = insert_booking({
        "shop_id": shop_id, "barber_id": data['barber_id'], "service_id": data['service_id'],
        "customer_id": data['customer_id'], "customer_name": call.from_user.full_name,
        "start_at": start_at, "end_at": start_at + timedelta(minutes=int(data.get('duration', 30)))
    })
    
    if booking_id:
        await call.message.edit_text(get_msg("success", lang=data.get("lang", "uz"), id=booking_id))
        await call.message.answer("🏠 Menu", reply_markup=main_menu_keyboard(lang=data.get("lang", "uz")))
        
        # NOTIFY THE SPECIFIC SHOP OWNER
        owner_id = get_shop_owner_id(shop_id)
        if owner_id:
            alert = f"🔔 Yangi Buyurtma (ID: {booking_id})\nMijoz: {call.from_user.full_name}\n🕒 Vaqt: {data['date']} {data['time']}"
            try: await bot.send_message(chat_id=owner_id, text=alert)
            except: pass
    else:
        await call.message.edit_text(get_msg("error_taken", lang=data.get("lang", "uz")))
    await state.clear()
