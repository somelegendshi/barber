import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\domain\slotting.py", "r", encoding="utf-8") as f:
    code = f.read()

# Fix the slot generation to support crossing midnight
old_logic = '''    for wh in day_work_hours:
        current_time = datetime.datetime.combine(date, wh['start_time'])
        end_time = datetime.datetime.combine(date, wh['end_time'])
        slot_step = datetime.timedelta(minutes=wh['slot_step_min'])
        service_duration = datetime.timedelta(minutes=service_duration_min)
        
        while current_time + service_duration <= end_time:'''

new_logic = '''    for wh in day_work_hours:
        current_time = datetime.datetime.combine(date, wh['start_time'])
        end_time = datetime.datetime.combine(date, wh['end_time'])
        
        # If end_time is less than or equal to start_time but not exactly equal (which might mean closed)
        # Actually, if it's 24 hours, it might be 00:00 to 00:00. 
        # But we set "24 Soat" to 00:00 - 23:59.
        # So if end_time < start_time, it means it crosses midnight!
        if wh['end_time'] < wh['start_time']:
            end_time += datetime.timedelta(days=1)
            
        slot_step = datetime.timedelta(minutes=wh['slot_step_min'])
        service_duration = datetime.timedelta(minutes=service_duration_min)
        
        while current_time + service_duration <= end_time:'''

code = code.replace(old_logic, new_logic)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\domain\slotting.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Fixed slotting logic for crossing midnight.")
