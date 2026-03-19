from datetime import date, datetime, time
from functools import lru_cache
from typing import Optional

import pytz

DEFAULT_TIMEZONE = "Asia/Tashkent"
TZ_TASHKENT = pytz.timezone(DEFAULT_TIMEZONE)


@lru_cache(maxsize=64)
def get_tz(timezone_name: Optional[str] = None):
    return pytz.timezone(timezone_name or DEFAULT_TIMEZONE)


def get_now(timezone_name: Optional[str] = None) -> datetime:
    """Get the current timestamp in the provided timezone."""
    return datetime.now(get_tz(timezone_name))


def get_today(timezone_name: Optional[str] = None) -> date:
    """Get the current date in the provided timezone."""
    return get_now(timezone_name).date()


def localize(dt: datetime, timezone_name: Optional[str] = None) -> datetime:
    """Attach or convert timezone information."""
    tz = get_tz(timezone_name)
    if dt.tzinfo is None:
        return tz.localize(dt)
    return dt.astimezone(tz)


def combine_date_time(day: date, clock: time, timezone_name: Optional[str] = None) -> datetime:
    return localize(datetime.combine(day, clock), timezone_name)


def to_local(dt: datetime, timezone_name: Optional[str] = None) -> datetime:
    """Convert any datetime to the provided timezone."""
    return localize(dt, timezone_name)

# Localization Maps
DAYS_UZ = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
DAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

def format_date_localized(dt: date, lang: str = "uz") -> str:
    """Returns 'Dushanba 16.02' or 'Понедельник 16.02'"""
    day_idx = dt.weekday()
    day_name = DAYS_UZ[day_idx] if lang == "uz" else DAYS_RU[day_idx]
    return f"{day_name} {dt.strftime('%d.%m')}"
