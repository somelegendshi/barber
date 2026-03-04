# Messages (Uzbek/Russian)

# HTML formatting used for bold/italics
WELCOME_MSG = """
👋 <b>Assalomu alaykum / Здравствуйте, {name}!</b>

💈 <b>Top Barber</b> botiga xush kelibsiz.
<i>Bizning xizmatlardan foydalanish uchun tilni tanlang:</i>

<i>Добро пожаловать! Для начала выберите язык:</i>
"""

LANG_SELECT = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский"
}

# Dynamic messages based on lang code
def get_msg(key, lang="uz", **kwargs):
    texts = {
        "select_service": {
            "uz": "✂️ <b>Xizmat turini tanlang:</b>",
            "ru": "✂️ <b>Выберите услугу:</b>"
        },
        "select_barber": {
            "uz": "💇‍♂️ <b>Ustani tanlang:</b>",
            "ru": "💇‍♂️ <b>Выберите мастера:</b>"
        },
        "select_date": {
            "uz": "📅 <b>Sanani tanlang:</b>",
            "ru": "📅 <b>Выберите дату:</b>"
        },
        "select_time": {
            "uz": "⏰ <b>Vaqtni tanlang:</b>",
            "ru": "⏰ <b>Выберите время:</b>"
        },
        "request_phone": {
            "uz": "📞 <b>Iltimos, telefon raqamingizni yuboring:</b>\n<i>Quyidagi tugmani bosing</i> 👇",
            "ru": "📞 <b>Пожалуйста, отправьте ваш номер телефона:</b>\n<i>Нажмите кнопку ниже</i> 👇"
        },
        "confirm": {
            "uz": "📝 <b>Tasdiqlash:</b>\n\n👤 Usta: <b>{barber}</b>\n✂️ Xizmat: <b>{service}</b>\n📅 Vaqt: <b>{date} {time}</b>\n📱 Tel: <b>{phone}</b>\n\nTasdiqlaysizmi?",
            "ru": "📝 <b>Подтверждение:</b>\n\n👤 Мастер: <b>{barber}</b>\n✂️ Услуга: <b>{service}</b>\n📅 Время: <b>{date} {time}</b>\n📱 Тел: <b>{phone}</b>\n\nПодтверждаете?"
        },
        "success": {
            "uz": "✅ <b>Band qilindi!</b>\n\n🆔 Buyurtma raqami: <code>{id}</code>\n📍 Biz sizni kutamiz!",
            "ru": "✅ <b>Забронировано!</b>\n\n🆔 Номер заказа: <code>{id}</code>\n📍 Мы ждем вас!"
        },
        "error_taken": {
            "uz": "🚫 <b>Kechirasiz!</b>\nBu vaqt oralig'ida allaqachon band qilingan.\nIltimos, boshqa vaqtni tanlang.",
            "ru": "🚫 <b>Извините!</b>\nЭто время уже занято.\nПожалуйста, выберите другое время."
        }
    }
    try:
        return texts.get(key, {}).get(lang, "Error").format(**kwargs)
    except KeyError:
        return texts.get(key, {}).get(lang, "Error")
