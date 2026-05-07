WELCOME_MSG = """
👋 <b>Assalomu alaykum / Здравствуйте, {name}!</b>

💈 <b>Top Barber</b> botiga xush kelibsiz.
<i>Davom etish uchun tilni tanlang.</i>

<i>Добро пожаловать! Для продолжения выберите язык.</i>
"""


def get_msg(key, lang="uz", **kwargs):
    texts = {
        "select_service": {
            "uz": "✂️ <b>Xizmatni tanlang:</b>",
            "ru": "✂️ <b>Выберите услугу:</b>",
        },
        "select_barber": {
            "uz": "💇‍♂️ <b>Ustani tanlang:</b>",
            "ru": "💇‍♂️ <b>Выберите мастера:</b>",
        },
        "select_date": {
            "uz": "📅 <b>Sanani tanlang:</b>",
            "ru": "📅 <b>Выберите дату:</b>",
        },
        "select_time": {
            "uz": "🕰 <b>Vaqtni tanlang:</b>",
            "ru": "🕰 <b>Выберите время:</b>",
        },
        "request_phone": {
            "uz": "📞 <b>Iltimos, telefon raqamingizni yuboring:</b>\n<i>Quyidagi tugmani bosing</i> 👇",
            "ru": "📞 <b>Пожалуйста, отправьте номер телефона:</b>\n<i>Нажмите кнопку ниже</i> 👇",
        },
        "confirm": {
            "uz": (
                "📝 <b>Tasdiqlash</b>\n\n"
                "👤 Usta: <b>{barber}</b>\n"
                "✂️ Xizmat: <b>{service}</b>\n"
                "📅 Vaqt: <b>{date} {time}</b>\n"
                "📱 Telefon: <b>{phone}</b>\n\n"
                "Tasdiqlaysizmi?"
            ),
            "ru": (
                "📝 <b>Подтверждение</b>\n\n"
                "👤 Мастер: <b>{barber}</b>\n"
                "✂️ Услуга: <b>{service}</b>\n"
                "📅 Время: <b>{date} {time}</b>\n"
                "📱 Телефон: <b>{phone}</b>\n\n"
                "Подтверждаете?"
            ),
        },
        "success": {
            "uz": "✅ <b>Band qilindi!</b>\n\n📌 Buyurtma raqami: <code>{id}</code>\nSizni kutamiz.",
            "ru": "✅ <b>Запись оформлена!</b>\n\n📌 Номер записи: <code>{id}</code>\nЖдём вас.",
        },
        "error_taken": {
            "uz": "🚫 <b>Kechirasiz.</b>\nBu vaqt allaqachon band.\nIltimos, boshqa vaqtni tanlang.",
            "ru": "🚫 <b>Извините.</b>\nЭто время уже занято.\nПожалуйста, выберите другое время.",
        },
        "error_unavailable": {
            "uz": "🚫 <b>Kechirasiz.</b>\nTanlangan vaqt endi mavjud emas.\nIltimos, qaytadan vaqt tanlang.",
            "ru": "🚫 <b>Извините.</b>\nВыбранное время больше недоступно.\nПожалуйста, выберите время заново.",
        },
    }
    try:
        return texts.get(key, {}).get(lang, "Error").format(**kwargs)
    except KeyError:
        return texts.get(key, {}).get(lang, "Error")
