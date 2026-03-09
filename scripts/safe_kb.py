import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\keyboards.py", "r", encoding="utf-8") as f:
    code = f.read()

# I will find the function def admin_schedule_keyboard(work_hours: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
# and replace it.

old_func_start = 'def admin_schedule_keyboard(work_hours: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:'
old_func_end = 'def admin_edit_day_keyboard(dow: int, wh_id: int = None) -> InlineKeyboardMarkup:'

parts = code.split(old_func_start)
prefix = parts[0]
suffix = old_func_end + parts[1].split(old_func_end)[1]

new_func = '''def admin_schedule_keyboard(work_hours: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    days_uz = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    kb = []
    
    # Sort just to be safe
    work_hours = sorted(work_hours, key=lambda x: x['dow'])
    
    for wh in work_hours:
        dow = wh['dow']
        day_name = days_uz[dow][:4] # Shorten name
        
        # Time format
        if wh['start_time'] == wh['end_time']:
            time_str = "Yopiq"
        else:
            time_str = f"{wh['start_time'].strftime('%H:%M')}-{wh['end_time'].strftime('%H:%M')}"
            
        btn_text = f"{day_name}: {time_str}"
        
        kb.append([
            InlineKeyboardButton(text=btn_text, callback_data="ignore"),
            InlineKeyboardButton(text="Tahrirlash", callback_data=f"edit_day_{dow}")
        ])
        
    kb.append([InlineKeyboardButton(text="Orqaga", callback_data="back_to_admin_settings")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

'''

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\keyboards.py", "w", encoding="utf-8") as f:
    f.write(prefix + new_func + suffix)

print("Rewritten admin_schedule_keyboard safely!")
