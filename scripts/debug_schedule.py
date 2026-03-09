import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "r", encoding="utf-8") as f:
    code = f.read()

old_code = '''
    wh = get_work_hours(barber_id)
    await call.message.edit_text("⏰ Ish vaqtini sozlash / Настройка графика:", reply_markup=admin_schedule_keyboard(wh))
'''

new_code = '''
    wh = get_work_hours(barber_id)
    msg = f"⏰ Ish vaqtini sozlash / Настройка графика: (Debug: Shop {shop_id}, Barber {barber_id}, WHs {len(wh)})"
    await call.message.edit_text(msg, reply_markup=admin_schedule_keyboard(wh))
'''

code = code.replace(old_code, new_code)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated admin_schedule_menu to include debug info.")
