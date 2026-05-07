import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.bot import handlers_start


class FakeMessage:
    def __init__(self):
        self.answers = []
        self.deleted = False

    async def answer(self, text, **kwargs):
        self.answers.append((text, kwargs))

    async def delete(self):
        self.deleted = True


class FakeCall:
    def __init__(self, data="lang_ru", user_id=123):
        self.data = data
        self.from_user = SimpleNamespace(id=user_id, full_name="Test User", username="test_user")
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, *args, **kwargs):
        self.answers.append((args, kwargs))


class FakeState:
    def __init__(self, data=None):
        self.data = dict(data or {})

    async def get_data(self):
        return dict(self.data)

    async def update_data(self, **kwargs):
        self.data.update(kwargs)


class LanguageFlowTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_language_command_shows_language_picker(self):
        message = FakeMessage()
        message.from_user = SimpleNamespace(id=123, language_code="uz")
        state = FakeState({"active_shop_id": 77})

        with patch.object(handlers_start, "get_customer_language", return_value=None):
            await handlers_start.cmd_language(message, state)

        self.assertEqual(message.answers[0][0], handlers_start.LANGUAGE_PROMPT)
        self.assertIn("reply_markup", message.answers[0][1])

    async def test_language_choice_persists_and_keeps_customer_shop_context(self):
        call = FakeCall("lang_ru")
        state = FakeState({"active_shop_id": 77, "is_admin": False})

        with (
            patch.object(handlers_start, "set_customer_language") as set_language,
            patch.object(handlers_start, "get_admin_shop_id", return_value=None),
            patch.object(handlers_start, "get_shop", return_value={"id": 77, "name": "BarberTop"}),
        ):
            await handlers_start.set_lang(call, state)

        set_language.assert_called_once_with(123, "Test User", "ru", username="test_user")
        self.assertTrue(call.message.deleted)
        self.assertEqual(state.data["lang"], "ru")
        self.assertFalse(state.data["is_admin"])
        self.assertIn("BarberTop", call.message.answers[0][0])

    async def test_language_choice_without_shop_does_not_show_booking_menu(self):
        call = FakeCall("lang_uz")
        state = FakeState()

        with (
            patch.object(handlers_start, "set_customer_language"),
            patch.object(handlers_start, "get_admin_shop_id", return_value=None),
            patch.object(handlers_start, "get_shop") as get_shop,
        ):
            await handlers_start.set_lang(call, state)

        get_shop.assert_not_called()
        self.assertIn("salon havolasi", call.message.answers[0][0])
        self.assertFalse(state.data["is_admin"])

    async def test_invalid_language_callback_is_rejected(self):
        call = FakeCall("lang_en")
        state = FakeState()

        with patch.object(handlers_start, "set_customer_language") as set_language:
            await handlers_start.set_lang(call, state)

        set_language.assert_not_called()
        self.assertEqual(call.answers[0][1], {"show_alert": True})


if __name__ == "__main__":
    unittest.main()
