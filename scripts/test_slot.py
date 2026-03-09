import datetime
from app.domain.slotting import generate_slots

wh = [{
    'dow': 0,
    'start_time': datetime.time(22, 0),
    'end_time': datetime.time(4, 0),
    'slot_step_min': 30
}]
bookings = []
time_off = []

slots = generate_slots(wh, bookings, time_off, 30, datetime.date(2026, 3, 9))
print("Slots:", slots)
