from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict

# --- MAIN MENU (REPLY KEYBOARD) ---
def main_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    if lang == "uz":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✂️ Xizmatga yozilish")],
                [KeyboardButton(text="📅 Mening buyurtmalarim"), KeyboardButton(text="📞 Biz bilan aloqa")],
                [KeyboardButton(text="⚙️ Sozlamalar")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✂️ Записаться на услугу")],
                [KeyboardButton(text="📅 Мои записи"), KeyboardButton(text="📞 Контакты")],
                [KeyboardButton(text="⚙️ Настройки")]
            ],
            resize_keyboard=True
        )

# --- ADMIN MENU (REPLY KEYBOARD) ---
def admin_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Special menu for Barber/Owner."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Bugun / Сегодня"), KeyboardButton(text="🗓 Ertaga / Завтра")],
            [KeyboardButton(text="📋 Barcha buyurtmalar / Все заказы")],
            [KeyboardButton(text="⛔ Vaqtni bloklash / Блокировка времени")],
            [KeyboardButton(text="⚙️ Do'kon Sozlamalari / Настройки Салона")],
            [KeyboardButton(text="👥 Mijoz rejimi / Режим клиента")]
        ],
        resize_keyboard=True
    )

# --- ADMIN SETTINGS SUB-MENUS ---

def admin_settings_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✂️ Xizmatlar (Services)", callback_data="admin_services")],
        [InlineKeyboardButton(text="⏰ Ish Vaqti (Schedule)", callback_data="admin_schedule")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="close_admin_settings")]
    ])

def admin_services_edit_keyboard(services: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    kb = []
    for s in services:
        kb.append([
            InlineKeyboardButton(text=f"🗑 {s['name']} ({s['duration_min']} min)", callback_data=f"del_service_{s['id']}")
        ])
    
    kb.append([InlineKeyboardButton(text="➕ Yangi Xizmat Qo'shish", callback_data="add_new_service")])
    kb.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_admin_settings")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_schedule_keyboard(work_hours: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    # 0=Mon, 6=Sun
    days_uz = ["Dush", "Sesh", "Chor", "Pay", "Juma", "Shan", "Yak"]
    kb = []
    
    work_hours.sort(key=lambda x: x['dow'])
    
    for wh in work_hours:
        day_name = days_uz[wh['dow']]
        time_str = f"{wh['start_time'].strftime('%H:%M')}-{wh['end_time'].strftime('%H:%M')}"
        
        # If closed (00:00-00:00)
        if wh['start_time'] == wh['end_time']:
            time_str = "Yopiq / Закрыто"

        kb.append([
            InlineKeyboardButton(text=f"{day_name}: {time_str}", callback_data="ignore"),
            InlineKeyboardButton(text="✏️", callback_data=f"edit_day_{wh['dow']}")
        ])
        
    kb.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_admin_settings")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_edit_day_keyboard(dow: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Dam olish kuni (Yopish)", callback_data=f"set_day_off_{dow}")],
        [InlineKeyboardButton(text="🟢 Standart (10:00-20:00)", callback_data=f"set_day_std_{dow}")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="admin_schedule")]
    ])

# --- OTHER KEYBOARDS ---

# Language Selection Keyboard
def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]
    ])

# Phone Request Keyboard (Reply Keyboard)
def phone_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    text = "📞 Telefon raqamni yuborish" if lang == "uz" else "📞 Отправить номер телефона"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Services Keyboard
def services_keyboard(services: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    """Create buttons for each service."""
    kb = []
    for service in services:
        kb.append([InlineKeyboardButton(
            text=f"{service['name']}",
            callback_data=f"service_{service['id']}"
        )])
        
    btn_text = "🚫 Bekor qilish" if lang == "uz" else "🚫 Отмена"
    kb.append([InlineKeyboardButton(text=btn_text, callback_data="cancel_flow")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Barbers Keyboard
def barbers_keyboard(barbers: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    """Create buttons for each barber."""
    kb = []
    for barber in barbers:
        kb.append([InlineKeyboardButton(
            text=f"👤 {barber['display_name']}",
            callback_data=f"barber_{barber['id']}"
        )])
        
    back_text = "⬅️ Xizmatlarga qaytish" if lang == "uz" else "⬅️ К услугам"
    kb.append([InlineKeyboardButton(text=back_text, callback_data="back_to_services")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Date Selection (Next 7 days)
def dates_keyboard(dates: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    """Create buttons for next 7 days."""
    kb = []
    for i in range(0, len(dates), 2):
        row = []
        row.append(InlineKeyboardButton(text=dates[i]['text'], callback_data=dates[i]['callback']))
        if i+1 < len(dates):
            row.append(InlineKeyboardButton(text=dates[i+1]['text'], callback_data=dates[i+1]['callback']))
        kb.append(row)
        
    back_text = "⬅️ Ustani o'zgartirish" if lang == "uz" else "⬅️ Сменить мастера"
    kb.append([InlineKeyboardButton(text=back_text, callback_data="back_to_barbers")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Slot Selection (Times)
def slots_keyboard(slots: List[str], lang: str = "uz") -> InlineKeyboardMarkup:
    """Create buttons for available times."""
    kb = []
    for i in range(0, len(slots), 3):
        row = []
        for j in range(3):
            if i+j < len(slots):
                row.append(InlineKeyboardButton(text=slots[i+j], callback_data=f"time_{slots[i+j]}"))
        kb.append(row)
    
    back_text = "⬅️ Sanani o'zgartirish" if lang == "uz" else "⬅️ Сменить дату"
    kb.append([InlineKeyboardButton(text=back_text, callback_data="back_to_dates")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Confirm Booking
def confirm_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Yes/No confirmation."""
    yes_text = "✅ Tasdiqlash" if lang == "uz" else "✅ Подтвердить"
    no_text = "❌ Bekor qilish" if lang == "uz" else "❌ Отмена"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=yes_text, callback_data="confirm_booking")],
        [InlineKeyboardButton(text=no_text, callback_data="cancel_booking")]
    ])

# Phone Confirmation (Keep or Change)
def phone_confirm_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    use_text = "✅ Shu raqamni ishlatish" if lang == "uz" else "✅ Использовать этот"
    change_text = "🔄 Boshqa raqam kiritish" if lang == "uz" else "🔄 Ввести другой"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=use_text, callback_data="use_existing_phone")],
        [InlineKeyboardButton(text=change_text, callback_data="change_phone")]
    ])

# My Booking Actions (Cancel / Reschedule)
def my_booking_keyboard(booking_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    cancel_text = "❌ Bekor qilish" if lang == "uz" else "❌ Отменить"
    resched_text = "🔄 Vaqtni o'zgartirish" if lang == "uz" else "🔄 Перенести"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=resched_text, callback_data=f"reschedule_{booking_id}")],
        [InlineKeyboardButton(text=cancel_text, callback_data=f"cancel_me_{booking_id}")]
    ])

# Admin Quick Actions
def admin_quick_block_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    lunch_text = "🍱 Tushlik (13:00-14:00)" if lang == "uz" else "🍱 Обед (13:00-14:00)"
    hour_text = "⛔ 1 soatga yopish" if lang == "uz" else "⛔ Закрыть на 1 час"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lunch_text, callback_data="block_lunch")],
        [InlineKeyboardButton(text=hour_text, callback_data="block_1h")]
    ])
