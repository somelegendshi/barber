import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.bot.notifications import _booking_message


class NotificationTextTestCase(unittest.TestCase):
    def test_booking_message_includes_customer_phone(self):
        text = _booking_message(
            title="New booking",
            booking_id=21,
            shop_name="BarberTop",
            barber_name="Solih",
            service_name="Haircut",
            customer_name="Bosithon",
            customer_phone="+998901234567",
            time_text="23.04 10:00",
        )

        self.assertIn("+998901234567", text)
        self.assertIn("Bosithon", text)


if __name__ == "__main__":
    unittest.main()
