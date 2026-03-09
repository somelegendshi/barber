import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "r", encoding="utf-8") as f:
    code = f.read()

# Make sure set_time_end processes the new callback format correctly
old_end = '''@router.callback_query(F.data.startswith("set_time_end_"))
async def set_time_end(call: types.CallbackQuery):
    parts = call.data.split("_")
    # format: set_time_end_STARTTIME_WHID_ENDTIME
    wh_id = int(parts[4])
    start_time = parts[3]
    end_time = parts[5]'''

new_end = '''@router.callback_query(F.data.startswith("set_time_end_"))
async def set_time_end(call: types.CallbackQuery):
    parts = call.data.split("_")
    # format: set_time_end_STARTTIME_WHID_ENDTIME
    # parts: ['set', 'time', 'end', '08:00', '123', '18:00']
    wh_id = int(parts[4])
    start_time = parts[3]
    end_time = parts[5]'''

# It's actually correct. parts[3] is start, parts[4] is wh_id, parts[5] is end. Let's make sure `set_day_24h_` handler is there.

if "set_day_24h_" not in code:
    handler_24h = '''
@router.callback_query(F.data.startswith("set_day_24h_"))
async def set_day_24h(call: types.CallbackQuery):
    dow = int(call.data.split("_")[3])
    shop_id = get_current_shop_id(call.from_user.id)
    barber_id = get_shop_barber_id(shop_id)
    
    update_day_schedule(barber_id, dow, "00:00", "23:59")
    
    await call.answer("✅ 24 Soat saqlandi")
    wh = get_work_hours(barber_id)
    await call.message.edit_text("⏰ Ish vaqtini sozlash / Настройка графика:", reply_markup=admin_schedule_keyboard(wh))
'''
    code += handler_24h
    with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("Added set_day_24h handler.")
else:
    print("24h handler already there.")
