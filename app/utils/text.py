import re
from typing import Optional

SUPPORTED_LANGUAGES = {"uz", "ru"}


def normalize_language_code(language_code: Optional[str]) -> Optional[str]:
    if not language_code:
        return None
    normalized = language_code.strip().lower()
    return normalized if normalized in SUPPORTED_LANGUAGES else None


def resolve_lang(*preferred_langs: Optional[str], telegram_lang: Optional[str] = None) -> str:
    for candidate in preferred_langs:
        normalized = normalize_language_code(candidate)
        if normalized:
            return normalized

    if (telegram_lang or "").strip().lower().startswith("ru"):
        return "ru"
    return "uz"


def normalize_phone(phone: str) -> Optional[str]:
    cleaned = re.sub(r"[^\d+]", "", phone or "")
    if cleaned.startswith("00"):
        cleaned = f"+{cleaned[2:]}"

    if cleaned.count("+") > 1 or ("+" in cleaned and not cleaned.startswith("+")):
        return None

    digits = cleaned[1:] if cleaned.startswith("+") else cleaned
    if not digits.isdigit() or not 7 <= len(digits) <= 15:
        return None

    return f"+{digits}" if cleaned.startswith("+") else digits
