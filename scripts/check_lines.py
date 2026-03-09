import re
with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "r", encoding="utf-8") as f:
    for line in f:
        if "@router.message(F.text" in line:
            print(line.strip())
