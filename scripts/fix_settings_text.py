import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "r", encoding="utf-8") as f:
    code = f.read()

# Fix the custom hours start to be cleaner text
code = code.replace(
    'await call.message.edit_text("Ish boshlanish vaqtini tanlang:\\nВыберите время начала работы:",',
    'await call.message.edit_text("⏰ Ish boshlanish vaqtini tanlang:\\n(Start time):",'
)

code = code.replace(
    'await call.message.edit_text(f"Boshlanish: {time_val}\\nEndi tugash vaqtini tanlang:\\nВыберите время окончания:",',
    'await call.message.edit_text(f"🟢 Boshlanish: {time_val}\\n🔴 Endi tugash vaqtini tanlang (End time):",'
)

# And fix the `edit_day_wh_` back logic which is missing!
# In keyboards.py, `edit_day_wh_{wh_id}` is used. Wait, what is the handler for `edit_day_wh_`?
# In edit_day_start:
# if len(data_parts) > 3 and data_parts[2] == "wh":
# it correctly parses wh_id.
# Let's check edit_day_start.
print("Text replacements done.")

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "w", encoding="utf-8") as f:
    f.write(code)
