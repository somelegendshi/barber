import unittest
import ast
from pathlib import Path

from app.bot.keyboards import admin_menu_keyboard, admin_settings_keyboard, main_menu_keyboard


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _handler_text_filters(*handler_paths):
    texts = set()
    for handler_path in handler_paths:
        tree = ast.parse((PROJECT_ROOT / handler_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
                continue
            if len(node.comparators) != 1 or not isinstance(node.comparators[0], ast.Constant):
                continue
            left = node.left
            if (
                isinstance(left, ast.Attribute)
                and left.attr == "text"
                and isinstance(left.value, ast.Name)
                and left.value.id == "F"
            ):
                texts.add(node.comparators[0].value)
    return texts


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

    def test_reply_keyboard_labels_have_matching_handlers(self):
        customer_texts = {
            button.text
            for lang in ("uz", "ru")
            for row in main_menu_keyboard(lang).keyboard
            for button in row
        }
        admin_texts = {
            button.text
            for lang in ("uz", "ru")
            for row in admin_menu_keyboard(lang).keyboard
            for button in row
        }
        registered_texts = _handler_text_filters(
            "app/bot/handlers_admin_settings.py",
            "app/bot/handlers_customer.py",
            "app/bot/handlers_owner.py",
            "app/bot/handlers_start.py",
        )

        self.assertTrue(customer_texts.issubset(registered_texts))
        self.assertTrue(admin_texts.issubset(registered_texts))


if __name__ == "__main__":
    unittest.main()
