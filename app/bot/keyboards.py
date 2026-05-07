from typing import Dict, List

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def _back_text(lang: str) -> str:
    return "⬅️ Orqaga" if lang == "uz" else "⬅️ Назад"


def _close_text(lang: str) -> str:
    return "❌ Yopish" if lang == "uz" else "❌ Закрыть"


def main_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    if lang == "uz":
        keyboard = [
            [KeyboardButton(text="✂️ Xizmatga yozilish")],
            [KeyboardButton(text="📅 Mening buyurtmalarim")],
            [KeyboardButton(text="⚙️ Sozlamalar")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="✂️ Записаться на услугу")],
            [KeyboardButton(text="📅 Мои записи")],
            [KeyboardButton(text="⚙️ Настройки")],
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def admin_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    if lang == "uz":
        keyboard = [
            [KeyboardButton(text="📆 Bugun"), KeyboardButton(text="🗓️ Ertaga")],
            [KeyboardButton(text="📋 Barcha buyurtmalar")],
            [KeyboardButton(text="⛔ Vaqtni bloklash")],
            [KeyboardButton(text="⚙️ Do'kon sozlamalari")],
            [KeyboardButton(text="👤 Mijoz rejimi")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="📆 Сегодня"), KeyboardButton(text="🗓️ Завтра")],
            [KeyboardButton(text="📋 Все заказы")],
            [KeyboardButton(text="⛔ Блокировка времени")],
            [KeyboardButton(text="⚙️ Настройки салона")],
            [KeyboardButton(text="👤 Режим клиента")],
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def customer_settings_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    if lang == "uz":
        rows = [
            [InlineKeyboardButton(text="🌐 Tilni o'zgartirish", callback_data="settings_language")],
            [InlineKeyboardButton(text="❓ Yordam", callback_data="settings_help")],
            [InlineKeyboardButton(text=_close_text(lang), callback_data="close_customer_settings")],
        ]
    else:
        rows = [
            [InlineKeyboardButton(text="🌐 Сменить язык", callback_data="settings_language")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="settings_help")],
            [InlineKeyboardButton(text=_close_text(lang), callback_data="close_customer_settings")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_settings_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    if lang == "uz":
        rows = [
            [InlineKeyboardButton(text="💈 Ustalar", callback_data="admin_barbers")],
            [InlineKeyboardButton(text="✂️ Xizmatlar", callback_data="admin_services")],
            [InlineKeyboardButton(text="🕒 Ish vaqti", callback_data="admin_schedule")],
            [InlineKeyboardButton(text="🔗 Bron havolasi", callback_data="admin_share_link")],
            [InlineKeyboardButton(text="❓ Yordam", callback_data="admin_help")],
            [InlineKeyboardButton(text=_close_text(lang), callback_data="close_admin_settings")],
        ]
    else:
        rows = [
            [InlineKeyboardButton(text="💈 Мастера", callback_data="admin_barbers")],
            [InlineKeyboardButton(text="✂️ Услуги", callback_data="admin_services")],
            [InlineKeyboardButton(text="🕒 График", callback_data="admin_schedule")],
            [InlineKeyboardButton(text="🔗 Ссылка для записи", callback_data="admin_share_link")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="admin_help")],
            [InlineKeyboardButton(text=_close_text(lang), callback_data="close_admin_settings")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_services_edit_keyboard(services: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    for service in services:
        rows.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"🗑️ O'chirish: {service['name']} ({service['duration_min']} min)"
                        if lang == "uz"
                        else
                        f"🗑️ Удалить: {service['name']} ({service['duration_min']} min)"
                    ),
                    callback_data=f"del_service_{service['id']}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="➕ Yangi xizmat qo'shish" if lang == "uz" else "➕ Добавить услугу",
                callback_data="add_new_service",
            )
        ]
    )
    rows.append([InlineKeyboardButton(text=_back_text(lang), callback_data="back_to_admin_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_barbers_keyboard(
    barbers: List[Dict],
    prefix: str,
    lang: str = "uz",
    back_callback: str = "back_to_admin_settings",
) -> InlineKeyboardMarkup:
    rows = []
    for barber in barbers:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"💈 {barber['display_name']}",
                    callback_data=f"{prefix}_{barber['id']}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=_back_text(lang), callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_barbers_manage_keyboard(barbers: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    for barber in barbers:
        tags = []
        if not barber.get("is_active", True):
            tags.append("off" if lang == "uz" else "off")
        if barber.get("notify_telegram_id"):
            tags.append("notify")
        if barber.get("has_future_bookings"):
            tags.append("bron" if lang == "uz" else "бронь")

        title = f"💈 {barber['display_name']}"
        if tags:
            title = f"{title} ({', '.join(tags)})"

        rows.append([InlineKeyboardButton(text=title, callback_data=f"barber_info_{barber['id']}")])
        if barber.get("is_active", True):
            rows.append(
                [
                    InlineKeyboardButton(
                        text="🔔 Telegram ID biriktirish" if lang == "uz" else "🔔 Привязать Telegram ID",
                        callback_data=f"bind_barber_tg_{barber['id']}",
                    )
                ]
            )
            rows.append(
                [
                    InlineKeyboardButton(
                        text="🗑️ O'chirish" if lang == "uz" else "🗑️ Отключить",
                        callback_data=f"disable_barber_{barber['id']}",
                    )
                ]
            )

    rows.append(
        [
            InlineKeyboardButton(
                text="➕ Yangi usta qo'shish" if lang == "uz" else "➕ Добавить мастера",
                callback_data="add_new_barber",
            )
        ]
    )
    rows.append([InlineKeyboardButton(text=_back_text(lang), callback_data="back_to_admin_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_schedule_keyboard(
    work_hours: List[Dict],
    barber_id: int,
    lang: str = "uz",
    back_callback: str = "admin_schedule",
) -> InlineKeyboardMarkup:
    days_uz = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    day_names = days_uz if lang == "uz" else days_ru

    rows = []
    for wh in sorted(work_hours, key=lambda item: item["dow"]):
        day_name = day_names[wh["dow"]][:4]
        if wh["start_time"] == wh["end_time"]:
            time_text = "Yopiq" if lang == "uz" else "Закрыто"
        else:
            time_text = f"{wh['start_time'].strftime('%H:%M')}-{wh['end_time'].strftime('%H:%M')}"

        rows.append(
            [
                InlineKeyboardButton(text=f"📅 {day_name}: {time_text}", callback_data=f"edit_day_wh_{wh['id']}"),
                InlineKeyboardButton(text="✏️", callback_data=f"edit_day_wh_{wh['id']}"),
            ]
        )

    rows.append([InlineKeyboardButton(text=_back_text(lang), callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_edit_day_keyboard(wh_id: int, barber_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🏖️ Dam olish kuni" if lang == "uz" else "🏖️ Выходной", callback_data=f"set_day_off_wh_{wh_id}")],
        [InlineKeyboardButton(text="🕙 Standart 10:00-20:00" if lang == "uz" else "🕙 Стандарт 10:00-20:00", callback_data=f"set_day_std_wh_{wh_id}")],
        [InlineKeyboardButton(text="🌙 24 soat 00:00-23:59" if lang == "uz" else "🌙 24 часа 00:00-23:59", callback_data=f"set_day_24h_wh_{wh_id}")],
        [InlineKeyboardButton(text="⏱️ Boshqa vaqt" if lang == "uz" else "⏱️ Другое время", callback_data=f"custom_hours_{wh_id}")],
        [InlineKeyboardButton(text=_back_text(lang), callback_data=f"schedule_barber_{barber_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_time_picker_keyboard(wh_id: int, picker_type: str, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    times = [f"{hour:02d}:00" for hour in range(24)] + [f"{hour:02d}:30" for hour in range(24)]
    times.sort()

    for index in range(0, len(times), 4):
        row = []
        for offset in range(4):
            if index + offset < len(times):
                value = times[index + offset]
                row.append(
                    InlineKeyboardButton(
                        text=value,
                        callback_data=f"set_time_{picker_type}_{wh_id}_{value}",
                    )
                )
        rows.append(row)

    rows.append([InlineKeyboardButton(text=_back_text(lang), callback_data=f"edit_day_wh_{wh_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_share_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_back_text(lang), callback_data="back_to_admin_settings")]]
    )


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            ]
        ]
    )


def phone_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    text = "📱 Telefon raqamni yuborish" if lang == "uz" else "📱 Отправить номер телефона"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def services_keyboard(services: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    for service in services:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✂️ {service['name']} • {service['duration_min']} min",
                    callback_data=f"service_{service['id']}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish" if lang == "uz" else "❌ Отмена", callback_data="cancel_flow")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def barbers_keyboard(barbers: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    for barber in barbers:
        rows.append([InlineKeyboardButton(text=f"💈 {barber['display_name']}", callback_data=f"barber_{barber['id']}")])
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Ustani o'zgartirish" if lang == "uz" else "⬅️ Назад к услугам",
                callback_data="back_to_services",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dates_keyboard(dates: List[Dict], lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    for index in range(0, len(dates), 2):
        row = [InlineKeyboardButton(text=dates[index]["text"], callback_data=dates[index]["callback"])]
        if index + 1 < len(dates):
            row.append(InlineKeyboardButton(text=dates[index + 1]["text"], callback_data=dates[index + 1]["callback"]))
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Ustani o'zgartirish" if lang == "uz" else "⬅️ Сменить мастера",
                callback_data="back_to_barbers",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def slots_keyboard(slots: List[str], lang: str = "uz") -> InlineKeyboardMarkup:
    rows = []
    for index in range(0, len(slots), 3):
        row = []
        for offset in range(3):
            if index + offset < len(slots):
                value = slots[index + offset]
                row.append(InlineKeyboardButton(text=f"🕒 {value}", callback_data=f"time_{value}"))
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Sanani o'zgartirish" if lang == "uz" else "⬅️ Сменить дату",
                callback_data="back_to_dates",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash" if lang == "uz" else "✅ Подтвердить", callback_data="confirm_booking")],
            [InlineKeyboardButton(text="❌ Bekor qilish" if lang == "uz" else "❌ Отмена", callback_data="cancel_booking")],
        ]
    )


def phone_confirm_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Shu raqamni ishlatish" if lang == "uz" else "✅ Использовать этот номер", callback_data="use_existing_phone")],
            [InlineKeyboardButton(text="✏️ Boshqa raqam kiritish" if lang == "uz" else "✏️ Ввести другой номер", callback_data="change_phone")],
        ]
    )


def my_booking_keyboard(booking_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Vaqtni o'zgartirish" if lang == "uz" else "🔁 Перенести", callback_data=f"reschedule_{booking_id}")],
            [InlineKeyboardButton(text="❌ Bekor qilish" if lang == "uz" else "❌ Отменить", callback_data=f"cancel_me_{booking_id}")],
        ]
    )


def admin_quick_block_keyboard(barber_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽️ Tushlik (13:00-14:00)" if lang == "uz" else "🍽️ Обед (13:00-14:00)", callback_data=f"block_lunch_{barber_id}")],
            [InlineKeyboardButton(text="⏳ 1 soatga yopish" if lang == "uz" else "⏳ Закрыть на 1 час", callback_data=f"block_1h_{barber_id}")],
            [InlineKeyboardButton(text="Boshqa sana/vaqt" if lang == "uz" else "Другая дата/время", callback_data=f"block_custom_{barber_id}")],
            [InlineKeyboardButton(text=_close_text(lang), callback_data="close_admin_settings")],
        ]
    )
