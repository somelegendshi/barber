import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "r", encoding="utf-8") as f:
    code = f.read()

# Fix cyrillic replacements
code = code.replace('F.text.contains("")', 'F.text.contains("Сегодня")')
code = code.replace('F.text.contains("-?\'?")', 'F.text.contains("Завтра")')
code = code.replace('F.text.contains("\'? <")', 'F.text.contains("Все заказы")')
code = code.replace('F.text.contains("? >?\'")', 'F.text.contains("Режим клиента")')

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Fixed cyrillic in handlers_owner.py")
