import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "r", encoding="utf-8") as f:
    code = f.read()

# Make sure get_work_hours handles missing days
# Wait, let's fix it right before admin_schedule_keyboard
old_menu = '''    wh = get_work_hours(barber_id)
    msg = f"⏰ Ish vaqtini sozlash / Настройка графика: (Debug: Shop {shop_id}, Barber {barber_id}, WHs {len(wh)})"
    await call.message.edit_text(msg, reply_markup=admin_schedule_keyboard(wh))'''

new_menu = '''    wh = get_work_hours(barber_id)
    
    # Auto-heal missing work hours
    if len(wh) < 7:
        existing_dows = [w['dow'] for w in wh]
        from app.db.conn import get_db
        with get_db() as cur:
            for day in range(7):
                if day not in existing_dows:
                    cur.execute(
                        "INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) VALUES (%s, %s, '10:00', '20:00', 30)",
                        (barber_id, day)
                    )
        wh = get_work_hours(barber_id)
        
    msg = f"⏰ Ish vaqtini sozlash / Настройка графика:"
    await call.message.edit_text(msg, reply_markup=admin_schedule_keyboard(wh))'''

code = code.replace(old_menu, new_menu)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Self-healing work_hours added.")
