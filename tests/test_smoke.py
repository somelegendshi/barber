import os
import sys
import unittest
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from app.db.conn import get_db
from app.scripts.init_db import initialize_production_db

initialize_production_db()


@unittest.skipUnless(os.getenv("DATABASE_URL"), "DATABASE_URL is not configured")
class SmokeTestCase(unittest.TestCase):
    def test_db_connection(self):
        with get_db() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
        self.assertEqual(row["ok"], 1)

    def test_existing_shops_have_barbers(self):
        with get_db() as cur:
            cur.execute("SELECT id FROM shops")
            shop_ids = [row["id"] for row in cur.fetchall()]

        for shop_id in shop_ids:
            with get_db() as cur:
                cur.execute("SELECT COUNT(*) AS total FROM barbers WHERE shop_id = %s", (shop_id,))
                row = cur.fetchone()
            self.assertGreater(row["total"], 0, f"Shop {shop_id} has no barbers.")


if __name__ == "__main__":
    unittest.main()
