import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "r", encoding="utf-8") as f:
    code = f.read()

# Add blocking logic if not present
block_handlers = '''
# --- BLOCKING TIME ---

@router.message(F.text.startswith("⏳ Vaqtni bloklash"))
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
'''

if "cb_block_lunch" not in code:
    code += block_handlers
    with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "w", encoding="utf-8") as f:
        f.write(code)
        
print("Added blocking logic to handlers_owner.py")
