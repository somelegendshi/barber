import sys
import unittest
from datetime import date, time
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.bot import handlers_owner


class FakeUser:
    id = 100001
    language_code = "uz"


class FakeMessage:
    def __init__(self):
        self.from_user = FakeUser()
        self.answers = []

    async def answer(self, text, **kwargs):
        self.answers.append((text, kwargs))


class FakeState:
    async def get_data(self):
        return {"lang": "uz"}


class AdminBookingListTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_all_bookings_starts_from_shop_local_midnight(self):
        captured = {}

        def fake_list_confirmed_bookings_from(shop_id, start_dt):
            captured["shop_id"] = shop_id
            captured["start_dt"] = start_dt
            return []

        with (
            patch.object(handlers_owner, "get_admin_shop_id", return_value=77),
            patch.object(handlers_owner, "get_shop", return_value={"timezone": "Asia/Tashkent"}),
            patch.object(handlers_owner, "get_today", return_value=date(2026, 4, 22)),
            patch.object(
                handlers_owner,
                "list_confirmed_bookings_from",
                side_effect=fake_list_confirmed_bookings_from,
            ),
        ):
            await handlers_owner.cmd_all(FakeMessage(), FakeState())

        self.assertEqual(captured["shop_id"], 77)
        self.assertEqual(captured["start_dt"].date(), date(2026, 4, 22))
        self.assertEqual(captured["start_dt"].time(), time.min)
        self.assertEqual(str(captured["start_dt"].tzinfo), "Asia/Tashkent")


if __name__ == "__main__":
    unittest.main()
