import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\domain\slotting.py", "r", encoding="utf-8") as f:
    code = f.read()

# Change typing signature
code = code.replace(
    '-> List[datetime.time]:',
    '-> List[datetime.datetime]:'
)

# Change return values
code = code.replace(
    'available_slots.append(slot_start.time())',
    'available_slots.append(slot_start)'
)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\domain\slotting.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated slotting.py to return datetime objects.")
