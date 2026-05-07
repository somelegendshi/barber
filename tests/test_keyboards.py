import unittest

from app.bot.keyboards import admin_menu_keyboard, admin_settings_keyboard, main_menu_keyboard


class KeyboardUxTestCase(unittest.TestCase):
    def test_customer_main_menu_keeps_emoji_labels(self):
        keyboard = main_menu_keyboard("uz").keyboard
        texts = [row[0].text for row in keyboard]
        self.assertEqual(
            texts,
            ["✂️ Xizmatga yozilish", "📅 Mening buyurtmalarim", "⚙️ Sozlamalar"],
        )

    def test_admin_menu_keeps_emoji_labels(self):
        keyboard = admin_menu_keyboard("uz").keyboard
        flat_texts = [button.text for row in keyboard for button in row]
        self.assertIn("📆 Bugun", flat_texts)
        self.assertIn("🗓️ Ertaga", flat_texts)
        self.assertIn("⚙️ Do'kon sozlamalari", flat_texts)

    def test_admin_settings_keyboard_keeps_emoji_labels(self):
        rows = admin_settings_keyboard("uz").inline_keyboard
        texts = [row[0].text for row in rows]
        self.assertEqual(
            texts,
            ["💈 Ustalar", "✂️ Xizmatlar", "🕒 Ish vaqti", "🔗 Bron havolasi", "❓ Yordam", "❌ Yopish"],
        )


if __name__ == "__main__":
    unittest.main()
