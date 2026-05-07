import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.bot import handlers_booking


class FakeMessage:
    def __init__(self):
        self.edits = []
        self.answers = []

    async def edit_text(self, text, **kwargs):
        self.edits.append((text, kwargs))

    async def answer(self, text, **kwargs):
        self.answers.append((text, kwargs))


class FakeCall:
    def __init__(self):
        self.message = FakeMessage()
        self.from_user = SimpleNamespace(full_name="Test User")
        self.answers = []

    async def answer(self, text, **kwargs):
        self.answers.append((text, kwargs))


class FakeState:
    def __init__(self, data):
        self.data = dict(data)

    async def get_data(self):
        return dict(self.data)

    async def clear(self):
        self.data.clear()

    async def update_data(self, **kwargs):
        self.data.update(kwargs)


class BookingFlowSafetyTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_finalize_booking_rejects_stale_slot_before_insert(self):
        state = FakeState(
            {
                "lang": "uz",
                "active_shop_id": 77,
                "service_id": 5,
                "barber_id": 9,
                "customer_id": 12,
                "date": "2026-04-23",
                "time": "10:00",
                "phone": "+998901234567",
            }
        )
        call = FakeCall()
        fake_bot = object()

        with (
            patch.object(handlers_booking, "get_shop", return_value={"name": "BarberTop", "timezone": "Asia/Tashkent"}),
            patch.object(handlers_booking, "get_service", return_value={"id": 5, "name": "Haircut", "duration_min": 30}),
            patch.object(handlers_booking, "get_barber", return_value={"id": 9, "display_name": "Solih"}),
            patch.object(handlers_booking, "_available_slot_labels", return_value=[]),
            patch.object(handlers_booking, "insert_booking") as insert_booking,
            patch.object(handlers_booking, "send_new_booking_notifications", new=AsyncMock()) as send_notifications,
        ):
            await handlers_booking.finalize_booking(call, state, fake_bot)

        insert_booking.assert_not_called()
        send_notifications.assert_not_awaited()
        self.assertTrue(call.message.edits)
        self.assertTrue(call.message.answers)

    async def test_finalize_booking_rejects_missing_state_before_lookup(self):
        state = FakeState({"lang": "uz", "active_shop_id": 77})
        call = FakeCall()

        with patch.object(handlers_booking, "get_shop") as get_shop:
            await handlers_booking.finalize_booking(call, state, object())

        get_shop.assert_not_called()
        self.assertTrue(call.answers)
        self.assertEqual(state.data, {"lang": "uz", "active_shop_id": 77})

    async def test_finalize_booking_rejects_invalid_date_before_insert(self):
        state = FakeState(
            {
                "lang": "uz",
                "active_shop_id": 77,
                "service_id": 5,
                "barber_id": 9,
                "customer_id": 12,
                "date": "bad-date",
                "time": "10:00",
            }
        )
        call = FakeCall()

        with (
            patch.object(handlers_booking, "get_shop", return_value={"name": "BarberTop", "timezone": "Asia/Tashkent"}),
            patch.object(handlers_booking, "get_service", return_value={"id": 5, "name": "Haircut", "duration_min": 30}),
            patch.object(handlers_booking, "get_barber", return_value={"id": 9, "display_name": "Solih"}),
            patch.object(handlers_booking, "insert_booking") as insert_booking,
        ):
            await handlers_booking.finalize_booking(call, state, object())

        insert_booking.assert_not_called()
        self.assertTrue(call.answers)


if __name__ == "__main__":
    unittest.main()
