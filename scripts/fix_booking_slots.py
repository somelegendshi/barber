import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_booking.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace slot string formatting
old_slot_strs = '''    slots = generate_slots(work_hours, naive_bookings, [], int(data.get('duration', 30)), selected_date)
    slot_strs = [s.strftime("%H:%M") for s in slots]
    
    if not slot_strs:
        await call.answer("Vaqt qolmadi", show_alert=True)
        return

    await call.message.edit_text(get_msg("select_time", lang=lang), reply_markup=slots_keyboard(slot_strs, lang=lang))'''

new_slot_strs = '''    slots = generate_slots(work_hours, naive_bookings, [], int(data.get('duration', 30)), selected_date)
    
    if not slots:
        await call.answer("Vaqt qolmadi", show_alert=True)
        return

    await call.message.edit_text(get_msg("select_time", lang=lang), reply_markup=slots_keyboard(slots, lang=lang))'''

code = code.replace(old_slot_strs, new_slot_strs)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_booking.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated handlers_booking to pass datetime list.")
