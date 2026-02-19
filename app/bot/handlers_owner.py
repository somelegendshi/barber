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
    # 1. Check Super Admin (ENV)
    owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    if str(user_id) in [oid.strip() for oid in owner_ids]:
        return True
    # 2. Check Database
    return get_current_shop_id_fixed(user_id) != 1 or user_id in [int(oid.strip()) for oid in owner_ids if oid.strip().isdigit()]

def get_current_shop_id(user_id: int) -> int:
    return get_current_shop_id_fixed(user_id)

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
    
    shop_id = get_current_shop_id(message.from_user.id)
    bookings = list_all_future_bookings(shop_id=shop_id)
    
    if not bookings:
        await message.answer("📅 Hozircha buyurtmalar yo'q.")
        return
    
    report = ["📅 <b>Barcha buyurtmalar:</b>\n"]
    
    current_date = None
    for b in bookings:
        # Group by date visually
        b_date = b['start_at'].strftime('%d.%m.%Y')
        if b_date != current_date:
            report.append(f"\n🔹 <b>{b_date}</b>")
            current_date = b_date
            
        time_str = b['start_at'].strftime("%H:%M")
        
        user_info = b['customer_name']
        details = []
        if b.get('customer_username'):
            details.append(f"@{b['customer_username']}")
        if b.get('customer_phone'):
            details.append(f"📞 {b['customer_phone']}")
            
        if details:
            user_info += f" ({', '.join(details)})"
        
        report.append(
            f"🆔 <code>{b['id']}</code> | 🕒 {time_str} — {b['barber_name']} | {user_info}"
        )
        
    await message.answer("\n".join(report))

@router.message(F.text == "👥 Mijoz rejimi / Режим клиента")
async def switch_to_client_mode(message: types.Message):
    if not is_owner(message.from_user.id): return
    await message.answer(
        "👥 Mijoz rejimiga o'tildi. Qaytish uchun /start ni bosing.",
        reply_markup=lang_keyboard()
    )

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, bot: Bot):
    if not is_owner(message.from_user.id): return

    try:
        args = message.text.split()
        if len(args) < 2:
            raise ValueError("Missing booking ID")
            
        booking_id = int(args[1])
        shop_id = get_current_shop_id(message.from_user.id)
        
        success = cancel_booking_db(booking_id, shop_id)
        if success:
            await message.answer(f"✅ Buyurtma {booking_id} bekor qilindi.")
        else:
            await message.answer(f"❌ Buyurtma topilmadi yoki allaqachon bekor qilingan.")
            
    except ValueError:
        await message.answer("⚠️ Ishlatish: /cancel <BOOKING_ID>")
    except Exception as e:
        await message.answer(f"⚠️ Xatolik yuz berdi: {str(e)}")

# --- BLOCKING LOGIC ---

@router.message(Command("block"))
async def cmd_block(message: types.Message):
    if not is_owner(message.from_user.id): return
    args = message.text.split()
    if len(args) == 1:
        await message.answer("⛔ Vaqtni bloklash menyusi:", reply_markup=admin_quick_block_keyboard())
        return

    try:
        if len(args) < 4:
             raise ValueError("Insufficient arguments")

        barber_id = int(args[1])
        time_str = args[2]
        duration = int(args[3])
        
        today = get_today()
        try:
            start_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
             await message.answer("⚠️ Vaqt formati noto'g'ri. HH:MM ishlating")
             return

        start_at = datetime.combine(today, start_time).astimezone(get_now().tzinfo)
        end_at = start_at + timedelta(minutes=duration)
        
        block_time_range(barber_id, start_at, end_at, reason="Owner Block")
        await message.answer(f"⛔ Vaqt bloklandi: {time_str}")
        
    except Exception as e:
        await message.answer(f"⚠️ Xatolik: {e}")

@router.message(F.text == "⛔ Vaqtni bloklash") # Fallback if text button used
@router.message(F.text == "⛔ Vaqtni bloklash / Блокировка времени")
async def show_block_options(message: types.Message):
    if not is_owner(message.from_user.id): return
    await message.answer("Tanlang / Выберите:", reply_markup=admin_quick_block_keyboard())

@router.callback_query(F.data == "block_lunch")
async def block_lunch_handler(call: types.CallbackQuery):
    shop_id = get_current_shop_id(call.from_user.id)
    barber_id = get_shop_barber_id(shop_id)
    
    if not barber_id:
        await call.answer("Usta topilmadi", show_alert=True)
        return
    
    today = get_today()
    start_time = datetime.strptime("13:00", "%H:%M").time()
    start_at = datetime.combine(today, start_time).astimezone(get_now().tzinfo)
    end_at = start_at + timedelta(hours=1)
    
    block_time_range(barber_id, start_at, end_at, reason="Lunch")
    await call.message.edit_text(f"✅ Bugun 13:00-14:00 bloklandi.")

@router.callback_query(F.data == "block_1h")
async def block_1h_handler(call: types.CallbackQuery):
    shop_id = get_current_shop_id(call.from_user.id)
    barber_id = get_shop_barber_id(shop_id)
    
    start_at = get_now()
    end_at = start_at + timedelta(hours=1)
    
    block_time_range(barber_id, start_at, end_at, reason="Instant Block")
    await call.message.edit_text(f"✅ Keyingi 1 soat bloklandi.")

async def list_bookings_for_date(message: types.Message, days_offset: int):
    if not is_owner(message.from_user.id): return
    
    target_date = get_today() + timedelta(days=days_offset)
    shop_id = get_current_shop_id(message.from_user.id)
    
    bookings = list_bookings_detailed(shop_id=shop_id, date=target_date)
    
    date_str = target_date.strftime('%d.%m')
    if not bookings:
        await message.answer(f"📅 {date_str}: Buyurtmalar yo'q.")
        return
        
    report = [f"📅 <b>Buyurtmalar ({date_str}):</b>\n"]
    
    for b in bookings:
        time_str = b['start_at'].strftime("%H:%M")
        
        contact_info = ""
        if b.get('customer_username'):
             contact_info += f"@{b['customer_username']} "
        if b.get('customer_phone'):
             contact_info += f"📞 {b['customer_phone']}\n"
        
        contact_line = f"\nℹ️ {contact_info}" if contact_info else ""

        report.append(
            f"🆔 <code>{b['id']}</code> | 🕒 {time_str} — {b['barber_name']}\n"
            f"👤 {b['customer_name']} ({b['service_name']})"
            f"{contact_line}"
        )
        
    await message.answer("\n".join(report))
