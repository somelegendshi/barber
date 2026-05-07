import unittest

from app.utils.text import normalize_phone, resolve_lang


class TextUtilsTestCase(unittest.TestCase):
    def test_resolve_lang_prefers_saved_choice(self):
        self.assertEqual(resolve_lang(None, "ru", telegram_lang="uz"), "ru")

    def test_resolve_lang_falls_back_to_telegram_locale(self):
        self.assertEqual(resolve_lang(None, None, telegram_lang="ru-RU"), "ru")

    def test_normalize_phone_accepts_common_formatting(self):
        self.assertEqual(normalize_phone("+998 (90) 123-45-67"), "+998901234567")

    def test_normalize_phone_supports_double_zero_prefix(self):
        self.assertEqual(normalize_phone("00998 90 123 45 67"), "+998901234567")

    def test_normalize_phone_rejects_invalid_input(self):
        self.assertIsNone(normalize_phone("phone-number"))


if __name__ == "__main__":
    unittest.main()
