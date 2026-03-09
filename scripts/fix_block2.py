import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace(
    'await call.message.edit_text("✅ Tushlik vaqti (13:00 - 14:00) bloklandi.\\nОбед (13:00 - 14:00) заблокирован.")',
    'await call.message.edit_text("✅ Tushlik vaqti (13:00 - 14:00) bloklandi.\\nОбед (13:00 - 14:00) заблокирован.")'
)

# Wait, my fix_blocking script had:
# await call.message.edit_text("✅ Tushlik vaqti (13:00 - 14:00) bloklandi.\nОбед (13:00 - 14:00) заблокирован.")
# That's a literal newline if I didn't use raw strings!
