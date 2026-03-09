import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "r", encoding="utf-8") as f:
    code = f.read()

# Add set_day_24h_
handler_24h = '''
@router.callback_query(F.data.startswith("set_day_24h_"))
async def set_day_24h(call: types.CallbackQuery):
    dow = int(call.data.split("_")[3])
    shop_id = get_current_shop_id(call.from_user.id)
    barber_id = get_shop_barber_id(shop_id)
    
    update_day_schedule(barber_id, dow, "00:00", "23:59")
    
    await call.answer("✅ 24 Soat (00:00 - 23:59)")
    wh = get_work_hours(barber_id)
    await call.message.edit_text("⏰ Ish vaqtini sozlash / Настройка графика:", reply_markup=admin_schedule_keyboard(wh))
'''

if "set_day_24h_" not in code:
    code += handler_24h

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Settings updated successfully.")
