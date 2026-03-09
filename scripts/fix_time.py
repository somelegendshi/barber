import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\keyboards.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace admin_edit_day_keyboard and admin_time_picker_keyboard
old_func_start = 'def admin_edit_day_keyboard(dow: int, wh_id: int = None) -> InlineKeyboardMarkup:'
old_func_end = '# --- OTHER KEYBOARDS ---'

parts = code.split(old_func_start)
prefix = parts[0]
suffix = old_func_end + parts[1].split(old_func_end)[1]

new_funcs = '''def admin_edit_day_keyboard(dow: int, wh_id: int = None) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="🌴 Dam olish kuni (Yopish)", callback_data=f"set_day_off_{dow}")],
        [InlineKeyboardButton(text="🏢 Standart (10:00-20:00)", callback_data=f"set_day_std_{dow}")],
        [InlineKeyboardButton(text="🌍 24 Soat (00:00-23:59)", callback_data=f"set_day_24h_{dow}")]
    ]
    if wh_id:
        kb.append([InlineKeyboardButton(text="⏳ Vaqtni tanlash (Custom)", callback_data=f"custom_hours_{wh_id}")])
    
    kb.append([InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="admin_schedule")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_time_picker_keyboard(wh_id: int, type: str) -> InlineKeyboardMarkup:
    """Type is 'start' or 'end_{start_time}'"""
    kb = []
    times = [f"{h:02d}:00" for h in range(0, 24)]
    times += [f"{h:02d}:30" for h in range(0, 24)]
    times.sort()
    
    for i in range(0, len(times), 4):
        row = []
        for j in range(4):
            if i+j < len(times):
                t = times[i+j]
                row.append(InlineKeyboardButton(text=t, callback_data=f"set_time_{type}_{wh_id}_{t}"))
        kb.append(row)
    
    kb.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"edit_day_wh_{wh_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

'''

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\keyboards.py", "w", encoding="utf-8") as f:
    f.write(prefix + new_funcs + suffix)

print("Updated keyboards.")
