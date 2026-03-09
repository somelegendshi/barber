import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for l in lines:
    if "✅ Tushlik vaqti" in l and 'bloklandi.' in l:
        new_lines.append('    await call.message.edit_text("✅ Tushlik vaqti (13:00 - 14:00) bloklandi.\\nОбед (13:00 - 14:00) заблокирован.")\n')
    elif "Обед (13:00 - 14:00) заблокирован" in l:
        pass # Skip the broken next line
    elif "✅ Hozirdan boshlab 1 soatga bloklandi" in l:
        new_lines.append('    await call.message.edit_text(f"✅ Hozirdan boshlab 1 soatga bloklandi (to {end_at.strftime(\'%H:%M\')}).\\nЗаблокировано на 1 час.")\n')
    elif "Заблокировано на 1 час" in l:
        pass
    else:
        new_lines.append(l)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
