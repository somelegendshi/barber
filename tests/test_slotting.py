import datetime
import unittest

from app.domain.slotting import generate_slots


class SlottingTestCase(unittest.TestCase):
    def test_time_off_blocks_slots(self):
        date_value = datetime.date(2026, 3, 20)
        work_hours = [
            {
                "dow": date_value.weekday(),
                "start_time": datetime.time(10, 0),
                "end_time": datetime.time(12, 0),
                "slot_step_min": 30,
            }
        ]
        time_off = [
            {
                "start_at": datetime.datetime(2026, 3, 20, 10, 30),
                "end_at": datetime.datetime(2026, 3, 20, 11, 0),
            }
        ]

        slots = generate_slots(work_hours, [], time_off, 30, date_value)
        slot_strings = [slot.strftime("%H:%M") for slot in slots]
        self.assertEqual(slot_strings, ["10:00", "11:00", "11:30"])

    def test_existing_booking_removes_overlap(self):
        date_value = datetime.date(2026, 3, 20)
        work_hours = [
            {
                "dow": date_value.weekday(),
                "start_time": datetime.time(10, 0),
                "end_time": datetime.time(12, 0),
                "slot_step_min": 30,
            }
        ]
        bookings = [
            {
                "start_at": datetime.datetime(2026, 3, 20, 10, 30),
                "end_at": datetime.datetime(2026, 3, 20, 11, 30),
            }
        ]

        slots = generate_slots(work_hours, bookings, [], 30, date_value)
        slot_strings = [slot.strftime("%H:%M") for slot in slots]
        self.assertEqual(slot_strings, ["10:00", "11:30"])

    def test_not_before_filters_past_slots(self):
        date_value = datetime.date(2026, 3, 20)
        work_hours = [
            {
                "dow": date_value.weekday(),
                "start_time": datetime.time(10, 0),
                "end_time": datetime.time(12, 0),
                "slot_step_min": 30,
            }
        ]

        slots = generate_slots(
            work_hours,
            [],
            [],
            30,
            date_value,
            not_before=datetime.datetime(2026, 3, 20, 10, 45),
        )
        slot_strings = [slot.strftime("%H:%M") for slot in slots]
        self.assertEqual(slot_strings, ["11:00", "11:30"])


if __name__ == "__main__":
    unittest.main()
