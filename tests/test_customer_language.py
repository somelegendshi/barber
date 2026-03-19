import os
import sys
import unittest
import uuid
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from app.db.conn import get_db
from app.db.repository import ensure_customer, get_customer_language, set_customer_language, sync_core_id_sequences
from app.scripts.init_db import initialize_production_db

initialize_production_db()


@unittest.skipUnless(os.getenv("DATABASE_URL"), "DATABASE_URL is not configured")
class CustomerLanguageTestCase(unittest.TestCase):
    def setUp(self):
        self.telegram_user_id = 9_000_000_000_000_000 + (uuid.uuid4().int % 1_000_000)

    def tearDown(self):
        with get_db() as cur:
            cur.execute("DELETE FROM customers WHERE telegram_user_id = %s", (self.telegram_user_id,))
        sync_core_id_sequences()

    def test_set_customer_language_persists_choice(self):
        set_customer_language(self.telegram_user_id, "Test User", "ru", username="test_user")

        self.assertEqual(get_customer_language(self.telegram_user_id), "ru")
        with get_db() as cur:
            cur.execute(
                "SELECT username FROM customers WHERE telegram_user_id = %s",
                (self.telegram_user_id,),
            )
            row = cur.fetchone()

        self.assertEqual(row["username"], "test_user")

    def test_ensure_customer_does_not_clear_existing_language(self):
        set_customer_language(self.telegram_user_id, "Test User", "uz")

        ensure_customer(self.telegram_user_id, "Updated User", username="updated_user")

        self.assertEqual(get_customer_language(self.telegram_user_id), "uz")


if __name__ == "__main__":
    unittest.main()
