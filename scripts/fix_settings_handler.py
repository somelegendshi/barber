import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "r", encoding="utf-8") as f:
    code = f.read()

code = re.sub(
    r'@router\.message\(F\.text == ".*Do\'kon Sozlamalari.*"\)',
    '@router.message(F.text.contains("Do\'kon Sozlamalari") | F.text.contains("Настройки Салона"))',
    code
)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Fixed admin settings handler.")
