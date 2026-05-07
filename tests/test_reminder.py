import contextlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.workers import reminder


class ReminderWorkerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_unlocks_same_connection_when_bot_setup_fails(self):
        fake_conn = object()

        with (
            patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123:abc"}, clear=False),
            patch.object(reminder, "get_db_connection", return_value=contextlib.nullcontext(fake_conn)),
            patch.object(reminder, "_try_lock", return_value=True) as try_lock,
            patch.object(reminder, "_unlock") as unlock,
            patch.object(reminder, "Bot", side_effect=RuntimeError("boom")),
        ):
            await reminder.send_reminders_task()

        try_lock.assert_called_once_with(fake_conn)
        unlock.assert_called_once_with(fake_conn)

    async def test_skips_run_without_unlock_when_lock_not_acquired(self):
        fake_conn = object()

        with (
            patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123:abc"}, clear=False),
            patch.object(reminder, "get_db_connection", return_value=contextlib.nullcontext(fake_conn)),
            patch.object(reminder, "_try_lock", return_value=False) as try_lock,
            patch.object(reminder, "_unlock") as unlock,
            patch.object(reminder, "Bot") as bot_cls,
        ):
            await reminder.send_reminders_task()

        try_lock.assert_called_once_with(fake_conn)
        unlock.assert_not_called()
        bot_cls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
