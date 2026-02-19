from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from datetime import datetime, timedelta
import os
from app.db.repository import list_bookings_detailed, list_all_future_bookings, cancel_booking_db, block_time_range
from app.db.repo_admin import get_shop_barber_id, get_current_shop_id_fixed
from app.utils.time import get_today, get_now
from app.bot.keyboards import main_menu_keyboard, lang_keyboard, admin_quick_block_keyboard
from app.bot.messages import WELCOME_MSG

router = Router()

def is_owner(user_id: int) -> bool:
    owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    if str(user_id) in [oid.strip() for oid in owner_ids]:
        return True
    return False # Only allow people in .env to see admin menu for now

def get_current_shop_id(user_id: int, message: types.Message = None) -> int:
    # If the user is a super admin, we should try to get the shop_id from their current session state
    # but for simplicity in this menu, we default to Shop 1 unless specified.
    return 1

# --- ADMIN MENU HANDLERS ---

@router.message(F.text == "📅 Bugun / Сегодня")
@router.message(Command("today"))
async def cmd_today(message: types.Message):
    await list_bookings_for_date(message, 0)

@router.message(F.text == "🗓 Ertaga / Завтра")
@router.message(Command("tomorrow"))
async def cmd_tomorrow(message: types.Message):
    await list_bookings_for_date(message, 1)

@router.message(F.text == "📋 Barcha buyurtmalar / Все заказы")
@router.message(Command("all"))
async def cmd_all(message: types.Message):
    if not is_owner(message.from_user.id): return
    
    # DEBUG: Let's list everything in the database for Shop 1 to prove it works
    bookings = list_all_future_bookings(shop_id=1)
    
    if not bookings:
        # Fallback: list EVERYTHING including past bookings for debug
        from app.db.conn import get_db
        with get_db() as cur:
            cur.execute("""
                SELECT b.id, b.customer_name, b.start_at, bar.display_name as barber_name, s.name as service_name
                FROM bookings b
                JOIN barbers bar ON b.barber_id = bar.id
                JOIN services s ON b.service_id = s.id
                WHERE b.shop_id = 1 AND b.status = 'CONFIRMED'
                ORDER BY b.start_at DESC
            """)
            bookings = cur.fetchall()

    if not bookings:
        await message.answer("📅 Hozircha buyurtmalar yo'q (Shop 1).")
        return
    
    report = ["📅 <b>Buyurtmalar Ro'yxati:</b>\n"]
    for b in bookings:
        b_date = b['start_at'].strftime('%d.%m %H:%M')
        report.append(f"🆔 <code>{b['id']}</code> | 🕒 {b_date} — {b['barber_name']} | {b['customer_name']}")
        
    await message.answer("\n".join(report))

@router.message(F.text == "👥 Mijoz rejimi / Режим клиента")
async def switch_to_client_mode(message: types.Message):
    if not is_owner(message.from_user.id): return
    await message.answer(
        "👥 Mijoz rejimiga o'tildi. Qaytish uchun /start ni bosing.",
        reply_markup=lang_keyboard()
    )

async def list_bookings_for_date(message: types.Message, days_offset: int):
    if not is_owner(message.from_user.id): return
    target_date = get_today() + timedelta(days=days_offset)
    bookings = list_bookings_detailed(shop_id=1, date=target_date)
    
    if not bookings:
        await message.answer(f"📅 {target_date.strftime('%d.%m')}: Buyurtmalar yo'q.")
        return
        
    report = [f"📅 <b>Buyurtmalar ({target_date.strftime('%d.%m')}):</b>\n"]
    for b in bookings:
        time_str = b['start_at'].strftime("%H:%M")
        report.append(f"🆔 <code>{b['id']}</code> | 🕒 {time_str} — {b['barber_name']}\n👤 {b['customer_name']} ({b['service_name']})")
        
    await message.answer("\n".join(report))
