import datetime
from typing import List, Dict

def generate_slots(
    work_hours: List[Dict],
    bookings: List[Dict],
    time_off: List[Dict],
    service_duration_min: int,
    date: datetime.date
) -> List[datetime.time]:
    """
    Core slotting engine.
    1. Filter WorkHours for the given date (weekday).
    2. Convert WorkHours to potential slot intervals (e.g., 9:00, 9:30, 10:00...).
    3. Remove slots that overlap with CONFIRMED bookings.
    4. Remove slots that overlap with TimeOff.
    5. Return available start times.
    """
    
    # Get work hours for this specific day of week (0=Mon, 6=Sun)
    day_work_hours = [wh for wh in work_hours if wh['dow'] == date.weekday()]
    
    if not day_work_hours:
        return []  # Barber doesn't work this day

    # Sort bookings and time_off by start time
    bookings.sort(key=lambda x: x['start_at'])
    time_off.sort(key=lambda x: x['start_at'])
    
    available_slots = []
    
    # Process each work window (e.g., could have multiple like 9-12 and 13-18)
    for wh in day_work_hours:
        current_time = datetime.datetime.combine(date, wh['start_time'])
        end_time = datetime.datetime.combine(date, wh['end_time'])
        slot_step = datetime.timedelta(minutes=wh['slot_step_min'])
        service_duration = datetime.timedelta(minutes=service_duration_min)
        
        while current_time + service_duration <= end_time:
            slot_start = current_time
            slot_end = current_time + service_duration
            
            # Check overlap with bookings
            conflict = False
            for booking in bookings:
                # Booking interval: [b_start, b_end)
                # Slot interval: [s_start, s_end)
                # Overlap logic: max(s_start, b_start) < min(s_end, b_end)
                if max(slot_start, booking['start_at']) < min(slot_end, booking['end_at']):
                    conflict = True
                    break
            
            if not conflict:
                # Check overlap with time_off
                for to in time_off:
                    if max(slot_start, to['start_at']) < min(slot_end, to['end_at']):
                        conflict = True
                        break
            
            if not conflict:
                available_slots.append(slot_start.time())
                
            current_time += slot_step
            
    return sorted(list(set(available_slots)))
