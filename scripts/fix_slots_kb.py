import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\keyboards.py", "r", encoding="utf-8") as f:
    code = f.read()

old_slots_kb = '''def slots_keyboard(slots: List[str], lang: str = "uz") -> InlineKeyboardMarkup:
    kb = []
    for i in range(0, len(slots), 3):
        row = []
        for j in range(3):
            if i+j < len(slots):
                row.append(InlineKeyboardButton(text=slots[i+j], callback_data=f"time_{slots[i+j]}"))
        kb.append(row)
    kb.append([InlineKeyboardButton(text="🔙 Sanani o'zgartirish" if lang == "uz" else "🔙 Изменить дату", callback_data="back_to_dates")])
    return InlineKeyboardMarkup(inline_keyboard=kb)'''

new_slots_kb = '''import datetime
def slots_keyboard(slots: List[datetime.datetime], lang: str = "uz") -> InlineKeyboardMarkup:
    kb = []
    for i in range(0, len(slots), 3):
        row = []
        for j in range(3):
            if i+j < len(slots):
                s = slots[i+j]
                text = s.strftime("%H:%M")
                if s.hour < 8 and s.time() != datetime.time(0,0): 
                    text += " (+1)" # rough indicator for next day
                
                # We will just pass the time as string and +1 flag if needed
                # Actually, best is passing full datetime
                cb = f"time_{s.strftime('%Y-%m-%d_%H:%M')}"
                row.append(InlineKeyboardButton(text=text, callback_data=cb))
        kb.append(row)
    kb.append([InlineKeyboardButton(text="🔙 Sanani o'zgartirish" if lang == "uz" else "🔙 Изменить дату", callback_data="back_to_dates")])
    return InlineKeyboardMarkup(inline_keyboard=kb)'''

code = code.replace(old_slots_kb, new_slots_kb)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\keyboards.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated slots_keyboard.")
