from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from app.bot.keyboards import (
    admin_settings_keyboard, 
    admin_services_edit_keyboard, 
    admin_schedule_keyboard, 
    admin_edit_day_keyboard,
    admin_time_picker_keyboard
)
from app.db.repository import list_services, get_work_hours
from app.db.repo_admin import (
    add_service_db, 
    delete_service_db, 
    update_day_schedule, 
    get_shop_barber_id,
    get_work_hour_by_id
)
from app.bot.handlers_owner import get_current_shop_id, is_owner
from datetime import datetime, timedelta
import os

router = Router()

class AdminStates(StatesGroup):
    ADD_SERVICE_NAME = State()
    ADD_SERVICE_DURATION = State()

@router.message(F.text.contains("Do'kon Sozlamalari") | F.text.contains("Настройки Салона"))
async def cmd_admin_settings(message: types.Message):
    if not is_owner(message.from_user.id): return
    await message.answer("🛠 Sozlamalar menyusi / Меню настроек:", reply_markup=admin_settings_keyboard())

@router.callback_query(F.data == "close_admin_settings")
async def close_settings(call: types.CallbackQuery):
    await call.message.delete()

@router.callback_query(F.data == "back_to_admin_settings")
async def back_settings(call: types.CallbackQuery):
    await call.message.edit_text("🛠 Sozlamalar menyusi / Меню настроек:", reply_markup=admin_settings_keyboard())

# --- SERVICES MANAGEMENT ---

@router.callback_query(F.data == "admin_services")
async def admin_services_menu(call: types.CallbackQuery):
    # FIXED: Use dynamic shop_id
    shop_id = get_current_shop_id(call.from_user.id)
    services = list_services(shop_id)
    await call.message.edit_text("✂️ Xizmatlarni boshqarish / Управление услугами:", reply_markup=admin_services_edit_keyboard(services))

@router.callback_query(F.data.startswith("del_service_"))
async def delete_service_handler(call: types.CallbackQuery):
    service_id = int(call.data.split("_")[2])
    # FIXED: Use dynamic shop_id
    shop_id = get_current_shop_id(call.from_user.id)
    
    delete_service_db(service_id, shop_id)
    
    services = list_services(shop_id)
    await call.message.edit_text("✅ O'chirildi / Удалено.\n✂️ Xizmatlarni boshqarish:", reply_markup=admin_services_edit_keyboard(services))

@router.callback_query(F.data == "add_new_service")
async def add_service_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Yangi xizmat nomini kiriting (Masalan: Soch bo'yash):\nВведите название новой услуги:")
    await state.set_state(AdminStates.ADD_SERVICE_NAME)

@router.message(AdminStates.ADD_SERVICE_NAME)
async def add_service_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Davomiyligi (daqiqa) kiriting (Masalan: 60):\nВведите длительность в минутах:")
    await state.set_state(AdminStates.ADD_SERVICE_DURATION)

@router.message(AdminStates.ADD_SERVICE_DURATION)
async def add_service_duration(message: types.Message, state: FSMContext):
    try:
        duration = int(message.text)
        data = await state.get_data()
        # FIXED: Use dynamic shop_id
        shop_id = get_current_shop_id(message.from_user.id)
        
        add_service_db(shop_id, data['name'], duration)
        
        await message.answer("✅ Xizmat qo'shildi / Услуга добавлена!")
        await message.answer("🛠 Sozlamalar menyusi:", reply_markup=admin_settings_keyboard())
        await state.clear()
    except ValueError:
        await message.answer("⚠️ Iltimos, faqat raqam kiriting (daqiqa).\nВведите только число.")

# --- SCHEDULE MANAGEMENT ---

@router.callback_query(F.data == "admin_schedule")
async def admin_schedule_menu(call: types.CallbackQuery):
    # FIXED: Use dynamic shop_id
    shop_id = get_current_shop_id(call.from_user.id)
    barber_id = get_shop_barber_id(shop_id)
    
    if not barber_id:
        await call.answer("Usta topilmadi / Мастер не найден", show_alert=True)
        return

    wh = get_work_hours(barber_id)
    msg = f"⏰ Ish vaqtini sozlash / Настройка графика: (Debug: Shop {shop_id}, Barber {barber_id}, WHs {len(wh)})"
    await call.message.edit_text(msg, reply_markup=admin_schedule_keyboard(wh))

@router.callback_query(F.data.startswith("edit_day_"))
async def edit_day_start(call: types.CallbackQuery):
    data_parts = call.data.split("_")
    
    # Check if we are coming from a WH record or just the DOW
    # If data is edit_day_wh_ID
    wh_id = None
    if len(data_parts) > 2 and data_parts[2] == "wh":
        wh_id = int(data_parts[3])
        wh = get_work_hour_by_id(wh_id)
        dow = wh['dow']
    else:
        dow = int(data_parts[2])
        # Try to find existing WH id
        shop_id = get_current_shop_id(call.from_user.id)
        barber_id = get_shop_barber_id(shop_id)
        whs = get_work_hours(barber_id)
        for w in whs:
            if w['dow'] == dow:
                wh_id = w['id']
                break

    days_uz = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    await call.message.edit_text(
        f"🗓 {days_uz[dow]} / {days_ru[dow]}:", 
        reply_markup=admin_edit_day_keyboard(dow, wh_id)
    )

@router.callback_query(F.data.startswith("custom_hours_"))
async def custom_hours_start(call: types.CallbackQuery):
    wh_id = int(call.data.split("_")[2])
    await call.message.edit_text("⏰ Ish boshlanish vaqtini tanlang:\n(Start time):", 
                                 reply_markup=admin_time_picker_keyboard(wh_id, "start"))

@router.callback_query(F.data.startswith("set_time_start_"))
async def set_time_start(call: types.CallbackQuery):
    parts = call.data.split("_")
    wh_id = int(parts[3])
    time_val = parts[4]
    
    await call.message.edit_text(f"🟢 Boshlanish: {time_val}\n🔴 Endi tugash vaqtini tanlang (End time):", 
                                 reply_markup=admin_time_picker_keyboard(wh_id, f"end_{time_val}"))

@router.callback_query(F.data.startswith("set_time_end_"))
async def set_time_end(call: types.CallbackQuery):
    parts = call.data.split("_")
    # format: set_time_end_STARTTIME_WHID_ENDTIME
    wh_id = int(parts[4])
    start_time = parts[3]
    end_time = parts[5]
    
    wh = get_work_hour_by_id(wh_id)
    update_day_schedule(wh['barber_id'], wh['dow'], start_time, end_time)
    
    await call.answer(f"✅ {start_time} - {end_time}")
    whs = get_work_hours(wh['barber_id'])
    await call.message.edit_text("⏰ Ish vaqtini sozlash / Настройка графика:", reply_markup=admin_schedule_keyboard(whs))

@router.callback_query(F.data.startswith("set_day_off_"))
async def set_day_off(call: types.CallbackQuery):
    dow = int(call.data.split("_")[3])
    # FIXED: Use dynamic shop_id
    shop_id = get_current_shop_id(call.from_user.id)
    barber_id = get_shop_barber_id(shop_id)
    
    update_day_schedule(barber_id, dow, "00:00", "00:00")
    
    await call.answer("✅ Yopildi / Закрыто")
    wh = get_work_hours(barber_id)
    msg = f"⏰ Ish vaqtini sozlash / Настройка графика: (Debug: Shop {shop_id}, Barber {barber_id}, WHs {len(wh)})"
    await call.message.edit_text(msg, reply_markup=admin_schedule_keyboard(wh))

@router.callback_query(F.data.startswith("set_day_std_"))
async def set_day_std(call: types.CallbackQuery):
    dow = int(call.data.split("_")[3])
    # FIXED: Use dynamic shop_id
    shop_id = get_current_shop_id(call.from_user.id)
    barber_id = get_shop_barber_id(shop_id)
    
    update_day_schedule(barber_id, dow, "10:00", "20:00")
    
    await call.answer("✅ 10:00-20:00")
    wh = get_work_hours(barber_id)
    msg = f"⏰ Ish vaqtini sozlash / Настройка графика: (Debug: Shop {shop_id}, Barber {barber_id}, WHs {len(wh)})"
    await call.message.edit_text(msg, reply_markup=admin_schedule_keyboard(wh))

@router.callback_query(F.data.startswith("set_day_24h_"))
async def set_day_24h(call: types.CallbackQuery):
    dow = int(call.data.split("_")[3])
    shop_id = get_current_shop_id(call.from_user.id)
    barber_id = get_shop_barber_id(shop_id)
    
    update_day_schedule(barber_id, dow, "00:00", "23:59")
    
    await call.answer("✅ 24 Soat (00:00 - 23:59)")
    wh = get_work_hours(barber_id)
    msg = f"⏰ Ish vaqtini sozlash / Настройка графика: (Debug: Shop {shop_id}, Barber {barber_id}, WHs {len(wh)})"
    await call.message.edit_text(msg, reply_markup=admin_schedule_keyboard(wh))
