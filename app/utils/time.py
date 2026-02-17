from datetime import datetime, date
import pytz

# Centralized Timezone Configuration
TZ_TASHKENT = pytz.timezone('Asia/Tashkent')

def get_now() -> datetime:
    """Get current timestamp in Tashkent time."""
    return datetime.now(TZ_TASHKENT)

def get_today() -> date:
    """Get current date in Tashkent."""
    return get_now().date()

def to_local(dt: datetime) -> datetime:
    """Convert any datetime to Tashkent time."""
    if dt.tzinfo is None:
        return TZ_TASHKENT.localize(dt)
    return dt.astimezone(TZ_TASHKENT)

# Localization Maps
DAYS_UZ = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
DAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

def format_date_localized(dt: date, lang: str = "uz") -> str:
    """Returns 'Dushanba 16.02' or 'Понедельник 16.02'"""
    day_idx = dt.weekday()
    day_name = DAYS_UZ[day_idx] if lang == "uz" else DAYS_RU[day_idx]
    return f"{day_name} {dt.strftime('%d.%m')}"
