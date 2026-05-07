def get_customer_help_text(lang: str = "uz") -> str:
    if lang == "ru":
        return (
            "<b>❓ Помощь клиенту</b>\n\n"
            "1. Нажмите '✂️ Записаться на услугу'.\n"
            "2. Выберите услугу, мастера, дату и время.\n"
            "3. Подтвердите номер телефона.\n"
            "4. Подтвердите запись.\n\n"
            "<b>📅 Мои записи</b>:\n"
            "- посмотреть активные записи\n"
            "- отменить запись\n"
            "- быстро записаться заново\n\n"
            "Если нужного времени нет, выберите другую дату или другого мастера."
        )
    return (
        "<b>❓ Mijoz uchun yordam</b>\n\n"
        "1. '✂️ Xizmatga yozilish' tugmasini bosing.\n"
        "2. Xizmat, usta, sana va vaqtni tanlang.\n"
        "3. Telefon raqamingizni tasdiqlang.\n"
        "4. Buyurtmani tasdiqlang.\n\n"
        "<b>📅 Mening buyurtmalarim</b> bo'limida:\n"
        "- faol buyurtmalarni ko'rasiz\n"
        "- buyurtmani bekor qilasiz\n"
        "- qayta yozilish uchun qulay ma'lumot olasiz\n\n"
        "Kerakli vaqt bo'lmasa, boshqa sana yoki boshqa ustani tanlang."
    )


def get_admin_help_text(lang: str = "uz") -> str:
    if lang == "ru":
        return (
            "<b>❓ Помощь администратору</b>\n\n"
            "<b>📆 Сегодня / 🗓️ Завтра</b>:\n"
            "смотреть ближайшие записи.\n\n"
            "<b>📋 Все заказы</b>:\n"
            "смотреть все будущие записи.\n\n"
            "<b>⛔ Блокировка времени</b>:\n"
            "быстро закрыть обед или 1 час для мастера.\n\n"
            "<b>⚙️ Настройки салона</b>:\n"
            "- добавить мастера\n"
            "- привязать Telegram ID мастера для уведомлений\n"
            "- после привязки мастер получает новые записи и отмены\n"
            "- добавить услугу\n"
            "- настроить график\n"
            "- получить ссылку для записи\n\n"
            "Чтобы получить Telegram ID мастера, попросите его отправить команду /my_id."
        )
    return (
        "<b>❓ Admin uchun yordam</b>\n\n"
        "<b>📆 Bugun / 🗓️ Ertaga</b>:\n"
        "yaqin buyurtmalarni ko'rasiz.\n\n"
        "<b>📋 Barcha buyurtmalar</b>:\n"
        "kelgusi barcha buyurtmalarni ko'rasiz.\n\n"
        "<b>⛔ Vaqtni bloklash</b>:\n"
        "usta uchun tushlik yoki 1 soatni tez bloklaysiz.\n\n"
        "<b>⚙️ Do'kon sozlamalari</b>:\n"
        "- yangi usta qo'shasiz\n"
        "- ustaga bildirishnoma Telegram ID biriktirasiz\n"
        "- ID biriktirilsa, usta yangi bron va bekor qilish xabarlarini oladi\n"
        "- xizmat qo'shasiz\n"
        "- ish vaqtini sozlaysiz\n"
        "- bron havolasini olasiz\n\n"
        "Ustaning Telegram ID sini olish uchun unga /my_id yuborishni ayting."
    )
