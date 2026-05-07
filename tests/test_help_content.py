import unittest

from app.bot.help_content import get_admin_help_text, get_customer_help_text


class HelpContentTestCase(unittest.TestCase):
    def test_customer_help_mentions_booking_flow(self):
        text = get_customer_help_text("uz")
        self.assertIn("Xizmatga yozilish", text)
        self.assertIn("Mening buyurtmalarim", text)

    def test_admin_help_mentions_barber_id_binding(self):
        text = get_admin_help_text("uz")
        self.assertIn("/my_id", text)
        self.assertIn("Telegram ID", text)


if __name__ == "__main__":
    unittest.main()
