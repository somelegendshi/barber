import datetime
import unittest

from app.bot.handlers_owner import _parse_custom_block_input
from app.utils.time import combine_date_time


class CustomBlockingTestCase(unittest.TestCase):
    def test_parses_full_day_block(self):
        now_dt = combine_date_time(datetime.date(2026, 5, 6), datetime.time(10, 0), "Asia/Tashkent")

        start_at, end_at = _parse_custom_block_input("2026-05-07", "Asia/Tashkent", now_dt=now_dt)

        self.assertEqual(start_at.strftime("%Y-%m-%d %H:%M"), "2026-05-07 00:00")
        self.assertEqual(end_at.strftime("%Y-%m-%d %H:%M"), "2026-05-08 00:00")

    def test_parses_custom_time_range(self):
        now_dt = combine_date_time(datetime.date(2026, 5, 6), datetime.time(10, 0), "Asia/Tashkent")

        start_at, end_at = _parse_custom_block_input(
            "2026-05-07 14:00-16:30",
            "Asia/Tashkent",
            now_dt=now_dt,
        )

        self.assertEqual(start_at.strftime("%Y-%m-%d %H:%M"), "2026-05-07 14:00")
        self.assertEqual(end_at.strftime("%Y-%m-%d %H:%M"), "2026-05-07 16:30")

    def test_rejects_past_block(self):
        now_dt = combine_date_time(datetime.date(2026, 5, 8), datetime.time(10, 0), "Asia/Tashkent")

        with self.assertRaises(ValueError):
            _parse_custom_block_input("2026-05-07", "Asia/Tashkent", now_dt=now_dt)

    def test_rejects_invalid_range_order(self):
        now_dt = combine_date_time(datetime.date(2026, 5, 6), datetime.time(10, 0), "Asia/Tashkent")

        with self.assertRaises(ValueError):
            _parse_custom_block_input("2026-05-07 16:30-14:00", "Asia/Tashkent", now_dt=now_dt)


if __name__ == "__main__":
    unittest.main()
