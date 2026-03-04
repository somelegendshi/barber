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

@router.message(F.text.contains("Bugun") | F.text.contains("Today") | Command("status"))
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

@router.message(F.text == "📋 Barcha buyurtmalar / Все заказы")
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

@router.message(F.text == "👥 Mijoz rejimi / Режим клиента")
async def switch_to_client_mode(message: types.Message):
    await message.answer("👥 Mijoz rejimiga o'tildi. Qaytish uchun /start ni bosing.", reply_markup=lang_keyboard())
