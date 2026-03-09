import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace(
    '@router.message(F.text.startswith("⏳ Vaqtni bloklash"))',
    '@router.message(F.text.contains("Vaqtni bloklash") | F.text.contains("bloklash") | F.text.contains("block"))'
)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated blocking text matching.")
