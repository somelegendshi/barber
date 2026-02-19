from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import os
from app.db.repository import list_bookings_detailed, list_all_future_bookings, cancel_booking_db, block_time_range, get_admin_shop_id
from app.db.repo_admin import get_shop_barber_id
from app.utils.time import get_today, get_now
from app.bot.keyboards import main_menu_keyboard, lang_keyboard, admin_quick_block_keyboard
from app.bot.messages import WELCOME_MSG

router = Router()

async def get_user_shop_id(user_id: int, state: FSMContext = None) -> int:
    # 1. Check if user is a shop admin in DB
    db_shop_id = get_admin_shop_id(user_id)
    if db_shop_id:
        return db_shop_id
    
    # 2. Check if user is Super Admin in ENV
    owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    if str(user_id) in [oid.strip() for oid in owner_ids]:
        if state:
            data = await state.get_data()
            return data.get("active_shop_id", 1)
        return 1
    
    return None

@router.message(F.text == "📅 Bugun / Сегодня")
@router.message(Command("today"))
async def cmd_today(message: types.Message, state: FSMContext):
    shop_id = await get_user_shop_id(message.from_user.id, state)
    if not shop_id: return
    await list_bookings_for_date(message, 0, shop_id)

@router.message(F.text == "🗓 Ertaga / Завтра")
@router.message(Command("tomorrow"))
async def cmd_tomorrow(message: types.Message, state: FSMContext):
    shop_id = await get_user_shop_id(message.from_user.id, state)
    if not shop_id: return
    await list_bookings_for_date(message, 1, shop_id)

@router.message(F.text == "📋 Barcha buyurtmalar / Все заказы")
@router.message(Command("all"))
async def cmd_all(message: types.Message, state: FSMContext):
    shop_id = await get_user_shop_id(message.from_user.id, state)
    if not shop_id: return
    
    bookings = list_all_future_bookings(shop_id=shop_id)
    
    if not bookings:
        await message.answer(f"📅 Hozircha buyurtmalar yo'q (Shop {shop_id}).")
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

async def list_bookings_for_date(message: types.Message, days_offset: int, shop_id: int):
    target_date = get_today() + timedelta(days=days_offset)
    bookings = list_bookings_detailed(shop_id=shop_id, date=target_date)
    
    date_str = target_date.strftime('%d.%m')
    if not bookings:
        await message.answer(f"📅 {date_str}: Buyurtmalar yo'q.")
        return
        
    report = [f"📅 <b>Buyurtmalar ({date_str}):</b>\n"]
    for b in bookings:
        time_str = b['start_at'].strftime("%H:%M")
        report.append(f"🆔 <code>{b['id']}</code> | 🕒 {time_str} — {b['barber_name']}\n👤 {b['customer_name']} ({b['service_name']})")
        
    await message.answer("\n".join(report))
