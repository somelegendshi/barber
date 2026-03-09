from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import os
from app.db.repository import (
    list_bookings_detailed, 
    list_all_future_bookings, 
    cancel_booking_db, 
    block_time_range, 
    get_admin_shop_id,
    list_barbers,
    list_services,
    get_shop
)
from app.db.repo_admin import get_shop_barber_id
from app.utils.time import get_today, get_now
from app.bot.keyboards import main_menu_keyboard, lang_keyboard, admin_quick_block_keyboard
from app.bot.messages import WELCOME_MSG

router = Router()

def is_owner(user_id: int) -> bool:
    owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    if str(user_id) in [oid.strip() for oid in owner_ids]:
        return True
    return get_admin_shop_id(user_id) is not None

async def get_user_shop_id(user_id: int, state: FSMContext = None) -> int:
    db_shop_id = get_admin_shop_id(user_id)
    if db_shop_id:
        return db_shop_id
    owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    if str(user_id) in [oid.strip() for oid in owner_ids]:
        if state:
            data = await state.get_data()
            return data.get("active_shop_id", 1)
        return 1
    return None

def get_current_shop_id(user_id: int) -> int:
    db_shop_id = get_admin_shop_id(user_id)
    if db_shop_id: return db_shop_id
    return 1

# --- SYSTEM HEALTH CHECK ---

@router.message(Command("status"))
@router.message(Command("status"))
async def cmd_system_health(message: types.Message, state: FSMContext):
    if not is_owner(message.from_user.id): return
    
    shop_id = await get_user_shop_id(message.from_user.id, state)
    shop = get_shop(shop_id)
    
    if not shop:
        await message.answer("❌ <b>XATOLIK:</b> Do'kon topilmadi.")
        return

    barbers = list_barbers(shop_id)
    services = list_services(shop_id)
    bookings = list_all_future_bookings(shop_id)

    health_report = (
        f"🏥 <b>Tizim Holati / Состояние Системы</b>\n\n"
        f"📍 Do'kon: <b>{shop['name']}</b> (ID: {shop_id})\n"
        f"👥 Ustalar: {len(barbers)}\n"
        f"✂️ Xizmatlar: {len(services)}\n"
        f"📅 Kelgusi buyurtmalar: {len(bookings)}\n\n"
        f"✅ <i>Tizim normal ishlamoqda.</i>"
    )
    await message.answer(health_report, parse_mode="HTML")

# --- ADMIN MENU HANDLERS ---

@router.message(F.text.contains("Bugun") | F.text.contains("Сегодня"))
@router.message(Command("today"))
async def cmd_today(message: types.Message, state: FSMContext):
    shop_id = await get_user_shop_id(message.from_user.id, state)
    if not shop_id: return
    
    today = get_today()
    bookings = list_bookings_detailed(shop_id, today)
    
    if not bookings:
        await message.answer("📅 Bugun uchun buyurtmalar yo'q / На сегодня заказов нет.")
        return
        
    report = ["📅 <b>Bugungi buyurtmalar / Заказы на сегодня:</b>\n"]
    for b in bookings:
        time_str = b['start_at'].strftime("%H:%M")
        phone = b.get('customer_phone') or b.get('customer_username') or "N/A"
        report.append(f"⏰ {time_str} | 💇‍♂️ {b['barber_name']} | 👤 {b['customer_name']} ({phone})")
        
    await message.answer("\n".join(report), parse_mode="HTML")

@router.message(F.text.contains("Ertaga") | F.text.contains("Завтра"))
@router.message(Command("tomorrow"))
async def cmd_tomorrow(message: types.Message, state: FSMContext):
    shop_id = await get_user_shop_id(message.from_user.id, state)
    if not shop_id: return
    
    tomorrow = get_today() + timedelta(days=1)
    bookings = list_bookings_detailed(shop_id, tomorrow)
    
    if not bookings:
        await message.answer("🗓 Ertaga uchun buyurtmalar yo'q / На завтра заказов нет.")
        return
        
    report = ["🗓 <b>Ertangi buyurtmalar / Заказы на завтра:</b>\n"]
    for b in bookings:
        time_str = b['start_at'].strftime("%H:%M")
        phone = b.get('customer_phone') or b.get('customer_username') or "N/A"
        report.append(f"⏰ {time_str} | 💇‍♂️ {b['barber_name']} | 👤 {b['customer_name']} ({phone})")
        
    await message.answer("\n".join(report), parse_mode="HTML")


@router.message(F.text.contains("Barcha buyurtmalar") | F.text.contains("Все заказы"))
@router.message(Command("all"))
async def cmd_all(message: types.Message, state: FSMContext):
    shop_id = await get_user_shop_id(message.from_user.id, state)
    if not shop_id: return
    
    bookings = list_all_future_bookings(shop_id=shop_id)
    
    if not bookings:
        await message.answer(f"📅 Hozircha yangi buyurtmalar yo'q (Shop {shop_id}).")
        return
    
    report = [f"📅 <b>Barcha buyurtmalar (Shop {shop_id}):</b>\n"]
    current_date = None
    for b in bookings:
        b_date = b['start_at'].strftime('%d.%m.%Y')
        if b_date != current_date:
            report.append(f"\n🔹 <b>{b_date}</b>")
            current_date = b_date
        time_str = b['start_at'].strftime("%H:%M")
        report.append(f"🆔 <code>{b['id']}</code> | 🕒 {time_str} — {b['barber_name']} | {b['customer_name']}")
        
    await message.answer("\n".join(report))

@router.message(F.text.contains("Mijoz rejimi") | F.text.contains("Режим клиента"))
async def switch_to_client_mode(message: types.Message):
    await message.answer("👥 Mijoz rejimiga o'tildi. Qaytish uchun /start ni bosing.", reply_markup=lang_keyboard())

# --- BLOCKING TIME ---

@router.message(F.text.contains("Vaqtni bloklash") | F.text.contains("bloklash") | F.text.contains("block"))
@router.message(Command("block"))
async def cmd_block_time(message: types.Message, state: FSMContext):
    shop_id = await get_user_shop_id(message.from_user.id, state)
    if not shop_id: return
    
    await message.answer("Vaqtni qanday bloklamoqchisiz? / Как вы хотите заблокировать время?", 
                         reply_markup=admin_quick_block_keyboard(lang="uz"))

@router.callback_query(F.data == "block_lunch")
async def cb_block_lunch(call: types.CallbackQuery):
    shop_id = get_current_shop_id(call.from_user.id)
    barber_id = get_shop_barber_id(shop_id)
    if not barber_id: return
    
    today = get_today()
    start_at = datetime.combine(today, datetime.min.time().replace(hour=13, minute=0))
    end_at = datetime.combine(today, datetime.min.time().replace(hour=14, minute=0))
    
    block_time_range(barber_id, start_at, end_at, "Tushlik / Обед")
    await call.message.edit_text("✅ Tushlik vaqti (13:00 - 14:00) bloklandi.\nОбед (13:00 - 14:00) заблокирован.")

@router.callback_query(F.data == "block_1h")
async def cb_block_1h(call: types.CallbackQuery):
    shop_id = get_current_shop_id(call.from_user.id)
    barber_id = get_shop_barber_id(shop_id)
    if not barber_id: return
    
    now = get_now()
    end_at = now + timedelta(hours=1)
    
    block_time_range(barber_id, now, end_at, "Vaqtincha yopiq / Временно закрыто")
    await call.message.edit_text(f"✅ Hozirdan boshlab 1 soatga bloklandi (to {end_at.strftime('%H:%M')}).\nЗаблокировано на 1 час.")
