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
from app.db.repository import (
    add_barber_db,
    assign_barber_notification_id,
    assign_shop_admin,
    create_default_shop_services,
    create_shop_db,
    deactivate_barber_db,
    delete_shop_db,
    get_admin_shop_id,
    get_shop,
    list_booking_notification_ids,
    resolve_shop_reference,
    sync_core_id_sequences,
)
from app.scripts.init_db import initialize_production_db

initialize_production_db()


@unittest.skipUnless(os.getenv("DATABASE_URL"), "DATABASE_URL is not configured")
class ShopManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.shop_id = create_shop_db(f"Test Shop {uuid.uuid4().hex[:8]}")
        create_default_shop_services(self.shop_id)

    def tearDown(self):
        if self.shop_id is not None:
            with get_db() as cur:
                cur.execute("DELETE FROM shops WHERE id = %s", (self.shop_id,))
        sync_core_id_sequences()

    def test_adding_barber_does_not_duplicate_services(self):
        add_barber_db(self.shop_id, "Ali")
        with get_db() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM services WHERE shop_id = %s", (self.shop_id,))
            first_total = cur.fetchone()["total"]

        add_barber_db(self.shop_id, "Vali")
        with get_db() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM services WHERE shop_id = %s", (self.shop_id,))
            second_total = cur.fetchone()["total"]

        self.assertEqual(first_total, 2)
        self.assertEqual(second_total, 2)

    def test_cannot_disable_last_active_barber(self):
        barber_id = add_barber_db(self.shop_id, "Ali")

        with self.assertRaises(ValueError):
            deactivate_barber_db(self.shop_id, barber_id)

    def test_can_disable_second_barber_when_another_active_remains(self):
        first_barber_id = add_barber_db(self.shop_id, "Ali")
        second_barber_id = add_barber_db(self.shop_id, "Vali")

        barber_name = deactivate_barber_db(self.shop_id, second_barber_id)

        self.assertEqual(barber_name, "Vali")
        with get_db() as cur:
            cur.execute("SELECT is_active FROM barbers WHERE id = %s", (first_barber_id,))
            first_status = cur.fetchone()["is_active"]
            cur.execute("SELECT is_active FROM barbers WHERE id = %s", (second_barber_id,))
            second_status = cur.fetchone()["is_active"]

        self.assertTrue(first_status)
        self.assertFalse(second_status)

    def test_barber_can_be_disabled_even_when_shop_admin_exists_separately(self):
        first_barber_id = add_barber_db(self.shop_id, "Ali")
        second_barber_id = add_barber_db(self.shop_id, "Vali")

        self.assertTrue(assign_shop_admin(self.shop_id, 987654321))
        barber_name = deactivate_barber_db(self.shop_id, first_barber_id)

        self.assertEqual(barber_name, "Ali")
        with get_db() as cur:
            cur.execute("SELECT is_active FROM barbers WHERE id = %s", (first_barber_id,))
            first_status = cur.fetchone()["is_active"]
            cur.execute("SELECT is_active FROM barbers WHERE id = %s", (second_barber_id,))
            second_status = cur.fetchone()["is_active"]

        self.assertFalse(first_status)
        self.assertTrue(second_status)
        self.assertEqual(get_admin_shop_id(987654321), self.shop_id)

    def test_notification_id_does_not_grant_admin_access(self):
        barber_id = add_barber_db(self.shop_id, "Ali")

        self.assertTrue(assign_barber_notification_id(barber_id, 1122334455))
        self.assertIsNone(get_admin_shop_id(1122334455))

    def test_booking_notifications_include_admin_and_booked_barber(self):
        admin_barber_id = add_barber_db(self.shop_id, "Ali")
        booked_barber_id = add_barber_db(self.shop_id, "Vali")

        self.assertTrue(assign_shop_admin(self.shop_id, 100001))
        self.assertTrue(assign_barber_notification_id(booked_barber_id, 200002))

        recipient_ids = list_booking_notification_ids(self.shop_id, booked_barber_id)
        self.assertEqual(recipient_ids, [100001, 200002])

    def test_shop_admin_assignment_grants_access_without_touching_barber_notify_id(self):
        admin_barber_id = add_barber_db(self.shop_id, "Ali")

        self.assertTrue(assign_shop_admin(self.shop_id, 300003))

        with get_db() as cur:
            cur.execute(
                "SELECT telegram_id, notify_telegram_id FROM barbers WHERE id = %s",
                (admin_barber_id,),
            )
            row = cur.fetchone()

        self.assertIsNone(row["telegram_id"])
        self.assertIsNone(row["notify_telegram_id"])
        self.assertEqual(get_admin_shop_id(300003), self.shop_id)

    def test_shop_gets_public_code_and_resolves_by_it(self):
        shop = get_shop(self.shop_id)

        self.assertIsNotNone(shop["public_code"])
        resolved = resolve_shop_reference(shop["public_code"])
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["id"], self.shop_id)

    def test_delete_shop_removes_shop_owned_records(self):
        add_barber_db(self.shop_id, "Ali")
        self.assertTrue(assign_shop_admin(self.shop_id, 444555666))

        deleted = delete_shop_db(self.shop_id)

        self.assertTrue(deleted)
        with get_db() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM shops WHERE id = %s", (self.shop_id,))
            self.assertEqual(cur.fetchone()["total"], 0)
            cur.execute("SELECT COUNT(*) AS total FROM barbers WHERE shop_id = %s", (self.shop_id,))
            self.assertEqual(cur.fetchone()["total"], 0)
            cur.execute("SELECT COUNT(*) AS total FROM services WHERE shop_id = %s", (self.shop_id,))
            self.assertEqual(cur.fetchone()["total"], 0)
            cur.execute("SELECT COUNT(*) AS total FROM shop_admins WHERE shop_id = %s", (self.shop_id,))
            self.assertEqual(cur.fetchone()["total"], 0)

        self.shop_id = None

    def test_delete_missing_shop_returns_false(self):
        self.assertFalse(delete_shop_db(-1))

    def test_sequence_sync_keeps_public_code_sequence_at_max_existing_value(self):
        extra_shop_id = create_shop_db(f"Temp Shop {uuid.uuid4().hex[:8]}")
        create_default_shop_services(extra_shop_id)
        with get_db() as cur:
            cur.execute("DELETE FROM shops WHERE id = %s", (extra_shop_id,))

        sync_core_id_sequences()

        with get_db() as cur:
            cur.execute("SELECT COALESCE(MAX(public_code), 0) AS max_code FROM shops")
            max_code = cur.fetchone()["max_code"]
            cur.execute("SELECT last_value FROM shops_public_code_seq")
            last_value = cur.fetchone()["last_value"]

        self.assertEqual(last_value, max_code if max_code > 0 else 1)


if __name__ == "__main__":
    unittest.main()
