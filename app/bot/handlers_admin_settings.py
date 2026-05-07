from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.bot.handlers_owner import require_owner_shop
from app.bot.help_content import get_admin_help_text
from app.bot.keyboards import (
    admin_barbers_keyboard,
    admin_barbers_manage_keyboard,
    admin_edit_day_keyboard,
    admin_schedule_keyboard,
    admin_services_edit_keyboard,
    admin_settings_keyboard,
    admin_share_keyboard,
    admin_time_picker_keyboard,
)
from app.bot.ui import safe_edit_text
from app.db.repo_admin import (
    add_service_db,
    delete_service_db,
    ensure_full_week_schedule,
    get_work_hour_by_id,
    update_day_schedule,
)
from app.db.repository import (
    add_barber_db,
    assign_barber_notification_id,
    deactivate_barber_db,
    get_barber,
    get_shop,
    list_barbers,
    list_barbers_admin,
    list_services,
)

router = Router()


class AdminStates(StatesGroup):
    ADD_SERVICE_NAME = State()
    ADD_SERVICE_DURATION = State()
    ADD_BARBER_NAME = State()
    BIND_BARBER_TELEGRAM_ID = State()


async def _reset_admin_state(state: FSMContext):
    data = await state.get_data()
    preserved = {
        key: value
        for key, value in data.items()
        if key in {"active_shop_id", "lang", "is_admin"}
    }
    await state.clear()
    if preserved:
        await state.update_data(**preserved)


async def _render_schedule(call: types.CallbackQuery, barber_id: int, lang: str):
    barber = get_barber(barber_id)
    if not barber:
        await call.answer("Usta topilmadi." if lang == "uz" else "Мастер не найден.", show_alert=True)
        return

    work_hours = ensure_full_week_schedule(barber_id)
    back_callback = "admin_schedule" if len(list_barbers(barber["shop_id"])) > 1 else "back_to_admin_settings"
    title = (
        f"<b>{barber['display_name']}</b> ish vaqti:"
        if lang == "uz"
        else
        f"<b>{barber['display_name']}</b> график:"
    )
    await safe_edit_text(
        call.message,
        title,
        callback=call,
        reply_markup=admin_schedule_keyboard(work_hours, barber_id, lang=lang, back_callback=back_callback),
        parse_mode="HTML",
    )


async def _render_barbers_menu(target, shop_id: int, lang: str, edit: bool = True):
    barbers = list_barbers_admin(shop_id)
    title = "<b>Ustalar ro'yxati</b>" if lang == "uz" else "<b>Список мастеров</b>"
    markup = admin_barbers_manage_keyboard(barbers, lang=lang)

    if edit and isinstance(target, types.CallbackQuery):
        await safe_edit_text(target.message, title, callback=target, reply_markup=markup, parse_mode="HTML")
    else:
        message = target.message if isinstance(target, types.CallbackQuery) else target
        await message.answer(title, reply_markup=markup, parse_mode="HTML")


@router.message(F.text == "⚙️ Do'kon sozlamalari")
@router.message(F.text == "⚙️ Настройки салона")
@router.message(F.text == "Do'kon sozlamalari")
@router.message(F.text == "Настройки салона")
async def cmd_admin_settings(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    title = "Sozlamalar menyusi:" if lang == "uz" else "Меню настроек:"
    await message.answer(title, reply_markup=admin_settings_keyboard(lang=lang))


@router.callback_query(F.data == "close_admin_settings")
async def close_settings(call: types.CallbackQuery):
    await call.message.delete()


@router.callback_query(F.data == "back_to_admin_settings")
async def back_settings(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    title = "Sozlamalar menyusi:" if lang == "uz" else "Меню настроек:"
    await safe_edit_text(call.message, title, callback=call, reply_markup=admin_settings_keyboard(lang=lang))


@router.callback_query(F.data == "admin_barbers")
async def admin_barbers_menu(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    await _render_barbers_menu(call, shop_id, lang)


@router.callback_query(F.data.startswith("barber_info_"))
async def barber_info(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    barber_id = int(call.data.split("_")[2])
    lang = (await state.get_data()).get("lang", "uz")
    barber = get_barber(barber_id, shop_id)
    if not barber:
        await call.answer("Usta topilmadi." if lang == "uz" else "Мастер не найден.", show_alert=True)
        return

    if lang == "uz":
        admin_status = "bor" if barber.get("telegram_id") else "yo'q"
        notify_status = barber.get("notify_telegram_id") or "biriktirilmagan"
        text = (
            f"Usta: {barber['display_name']}\n"
            f"Admin login ID: {admin_status}\n"
            f"Bildirishnoma ID: {notify_status}"
        )
    else:
        admin_status = "есть" if barber.get("telegram_id") else "нет"
        notify_status = barber.get("notify_telegram_id") or "не привязан"
        text = (
            f"Мастер: {barber['display_name']}\n"
            f"Admin login ID: {admin_status}\n"
            f"ID для уведомлений: {notify_status}"
        )
    await call.answer(text, show_alert=True)


@router.callback_query(F.data.startswith("bind_barber_tg_"))
async def bind_barber_tg_start(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    barber_id = int(call.data.split("_")[3])
    lang = (await state.get_data()).get("lang", "uz")
    barber = get_barber(barber_id, shop_id)
    if not barber:
        await call.answer("Usta topilmadi." if lang == "uz" else "Мастер не найден.", show_alert=True)
        return

    await state.update_data(bind_barber_id=barber_id)
    current_id = barber.get("notify_telegram_id")
    text = (
        f"<b>{barber['display_name']}</b> uchun Telegram ID yuboring.\n\n"
        f"Ustaga /my_id yuborishni ayting.\n"
        f"Hozirgi ID: <code>{current_id}</code>" if current_id else
        f"<b>{barber['display_name']}</b> uchun Telegram ID yuboring.\n\nUstaga /my_id yuborishni ayting."
    ) if lang == "uz" else (
        f"Отправьте Telegram ID для <b>{barber['display_name']}</b>.\n\n"
        f"Попросите мастера отправить /my_id.\n"
        f"Текущий ID: <code>{current_id}</code>" if current_id else
        f"Отправьте Telegram ID для <b>{barber['display_name']}</b>.\n\nПопросите мастера отправить /my_id."
    )
    await call.message.answer(text, parse_mode="HTML")
    await state.set_state(AdminStates.BIND_BARBER_TELEGRAM_ID)
    await call.answer()


@router.message(AdminStates.BIND_BARBER_TELEGRAM_ID)
async def bind_barber_tg_finish(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")
    barber_id = data.get("bind_barber_id")
    if not barber_id:
        await _reset_admin_state(state)
        await message.answer("Session tugadi." if lang == "uz" else "Сессия завершена.")
        return

    text_value = (message.text or "").strip()
    if not text_value.isdigit():
        await message.answer("Faqat raqamlardan iborat Telegram ID yuboring." if lang == "uz" else "Отправьте Telegram ID только цифрами.")
        return

    barber = get_barber(barber_id, shop_id)
    if not barber:
        await _reset_admin_state(state)
        await message.answer("Usta topilmadi." if lang == "uz" else "Мастер не найден.")
        return

    success = assign_barber_notification_id(barber_id, int(text_value))
    if not success:
        await message.answer("Telegram ID saqlanmadi." if lang == "uz" else "Не удалось сохранить Telegram ID.")
        return

    await _reset_admin_state(state)
    await message.answer(
        f"{barber['display_name']} uchun bildirishnoma ID saqlandi."
        if lang == "uz"
        else
        f"ID уведомлений для {barber['display_name']} сохранён."
    )
    await _render_barbers_menu(message, shop_id, lang, edit=False)


@router.callback_query(F.data == "add_new_barber")
async def add_barber_start(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    await state.update_data(admin_shop_id=shop_id)
    await call.message.delete()
    await call.message.answer("Yangi ustaning ismini kiriting:" if lang == "uz" else "Введите имя нового мастера:")
    await state.set_state(AdminStates.ADD_BARBER_NAME)


@router.message(AdminStates.ADD_BARBER_NAME)
async def add_barber_name(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    barber_name = (message.text or "").strip()
    if not barber_name:
        await message.answer("Ism bo'sh bo'lmasin." if lang == "uz" else "Имя не должно быть пустым.")
        return

    add_barber_db(shop_id, barber_name)
    await _reset_admin_state(state)
    await message.answer("Usta qo'shildi." if lang == "uz" else "Мастер добавлен.")
    await _render_barbers_menu(message, shop_id, lang, edit=False)


@router.callback_query(F.data.startswith("disable_barber_"))
async def disable_barber(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    barber_id = int(call.data.split("_")[2])
    lang = (await state.get_data()).get("lang", "uz")

    try:
        barber_name = deactivate_barber_db(shop_id, barber_id)
    except ValueError as exc:
        error_text = str(exc)
        if "At least one active barber" in error_text:
            text = "Kamida bitta faol usta qolishi kerak." if lang == "uz" else "В салоне должен остаться хотя бы один активный мастер."
        elif "Assign another admin" in error_text:
            text = "Bu admin usta. Avval boshqa admin tayinlang." if lang == "uz" else "Это админ-мастер. Сначала назначьте другого админа."
        else:
            text = "Bu ustada hali kelgusi buyurtmalar bor." if lang == "uz" else "У этого мастера ещё есть будущие записи."
        await call.answer(text, show_alert=True)
        return

    if not barber_name:
        await call.answer("Usta topilmadi." if lang == "uz" else "Мастер не найден.", show_alert=True)
        return

    await call.answer(f"{barber_name} o'chirildi." if lang == "uz" else f"{barber_name} отключён.")
    await _render_barbers_menu(call, shop_id, lang)


@router.callback_query(F.data == "admin_services")
async def admin_services_menu(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    services = list_services(shop_id)
    title = "Xizmatlarni boshqarish:" if lang == "uz" else "Управление услугами:"
    await safe_edit_text(call.message, title, callback=call, reply_markup=admin_services_edit_keyboard(services, lang=lang))


@router.callback_query(F.data.startswith("del_service_"))
async def delete_service_handler(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    service_id = int(call.data.split("_")[2])
    lang = (await state.get_data()).get("lang", "uz")
    deleted = delete_service_db(service_id, shop_id)
    if not deleted:
        await call.answer("Xizmat topilmadi." if lang == "uz" else "Услуга не найдена.", show_alert=True)
        return

    services = list_services(shop_id)
    title = "Xizmat o'chirildi." if lang == "uz" else "Услуга отключена."
    await safe_edit_text(call.message, title, callback=call, reply_markup=admin_services_edit_keyboard(services, lang=lang))


@router.callback_query(F.data == "add_new_service")
async def add_service_start(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    await state.update_data(admin_shop_id=shop_id)
    await call.message.delete()
    await call.message.answer("Yangi xizmat nomini kiriting:" if lang == "uz" else "Введите название новой услуги:")
    await state.set_state(AdminStates.ADD_SERVICE_NAME)


@router.message(AdminStates.ADD_SERVICE_NAME)
async def add_service_name(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    name = (message.text or "").strip()
    if not name:
        await message.answer("Nom bo'sh bo'lmasligi kerak." if lang == "uz" else "Название не должно быть пустым.")
        return

    await state.update_data(name=name, admin_shop_id=shop_id)
    await message.answer(
        "Davomiyligini daqiqada kiriting (masalan: 30):"
        if lang == "uz"
        else
        "Введите длительность в минутах (например: 30):"
    )
    await state.set_state(AdminStates.ADD_SERVICE_DURATION)


@router.message(AdminStates.ADD_SERVICE_DURATION)
async def add_service_duration(message: types.Message, state: FSMContext):
    shop_id = await require_owner_shop(message, state)
    if not shop_id:
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")

    try:
        duration = int(message.text)
        add_service_db(shop_id, data["name"], duration)
        await message.answer("Xizmat qo'shildi." if lang == "uz" else "Услуга добавлена.")
        await _reset_admin_state(state)
        await message.answer("Sozlamalar menyusi:" if lang == "uz" else "Меню настроек:", reply_markup=admin_settings_keyboard(lang=lang))
    except ValueError as exc:
        await message.answer(f"{exc}")


@router.callback_query(F.data == "admin_schedule")
async def admin_schedule_menu(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    barbers = list_barbers(shop_id)
    if not barbers:
        await call.answer("Faol ustalar topilmadi." if lang == "uz" else "Активные мастера не найдены.", show_alert=True)
        return

    if len(barbers) == 1:
        await _render_schedule(call, barbers[0]["id"], lang)
        return

    text = "Qaysi ustaning jadvalini tahrirlaymiz?" if lang == "uz" else "Какого мастера редактируем?"
    await safe_edit_text(call.message, text, callback=call, reply_markup=admin_barbers_keyboard(barbers, prefix="schedule_barber", lang=lang))


@router.callback_query(F.data.startswith("schedule_barber_"))
async def schedule_barber_selected(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    barber_id = int(call.data.split("_")[2])
    lang = (await state.get_data()).get("lang", "uz")
    barber = get_barber(barber_id, shop_id)
    if not barber:
        await call.answer("Usta topilmadi." if lang == "uz" else "Мастер не найден.", show_alert=True)
        return

    await _render_schedule(call, barber_id, lang)


@router.callback_query(F.data.startswith("edit_day_wh_"))
async def edit_day_start(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    wh_id = int(call.data.split("_")[3])
    lang = (await state.get_data()).get("lang", "uz")
    wh = get_work_hour_by_id(wh_id)
    barber = get_barber(wh["barber_id"], shop_id) if wh else None
    if not wh or not barber:
        await call.answer("Jadval topilmadi." if lang == "uz" else "График не найден.", show_alert=True)
        return

    days_uz = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    days = days_uz if lang == "uz" else days_ru

    await safe_edit_text(
        call.message,
        f"{days[wh['dow']]} • <b>{barber['display_name']}</b>",
        callback=call,
        reply_markup=admin_edit_day_keyboard(wh_id, barber["id"], lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("custom_hours_"))
async def custom_hours_start(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    wh_id = int(call.data.split("_")[2])
    lang = (await state.get_data()).get("lang", "uz")
    wh = get_work_hour_by_id(wh_id)
    barber = get_barber(wh["barber_id"], shop_id) if wh else None
    if not wh or not barber:
        await call.answer("Jadval topilmadi." if lang == "uz" else "График не найден.", show_alert=True)
        return

    await safe_edit_text(
        call.message,
        "Ish boshlanish vaqtini tanlang:" if lang == "uz" else "Выберите время начала:",
        callback=call,
        reply_markup=admin_time_picker_keyboard(wh_id, "start", lang=lang),
    )


@router.callback_query(F.data.startswith("set_time_start_"))
async def set_time_start(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    wh_id = int(parts[3])
    time_val = parts[4]
    lang = (await state.get_data()).get("lang", "uz")

    await safe_edit_text(
        call.message,
        f"Boshlanish: {time_val}\nEndi tugash vaqtini tanlang:"
        if lang == "uz"
        else
        f"Начало: {time_val}\nТеперь выберите время окончания:",
        callback=call,
        reply_markup=admin_time_picker_keyboard(wh_id, f"end_{time_val}", lang=lang),
    )


@router.callback_query(F.data.startswith("set_time_end_"))
async def set_time_end(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    parts = call.data.split("_")
    start_time = parts[3]
    wh_id = int(parts[4])
    end_time = parts[5]

    lang = (await state.get_data()).get("lang", "uz")
    wh = get_work_hour_by_id(wh_id)
    barber = get_barber(wh["barber_id"], shop_id) if wh else None
    if not wh or not barber:
        await call.answer("Jadval topilmadi." if lang == "uz" else "График не найден.", show_alert=True)
        return

    try:
        update_day_schedule(wh["barber_id"], wh["dow"], start_time, end_time)
    except ValueError as exc:
        await call.answer(str(exc), show_alert=True)
        return

    await call.answer(f"{start_time} - {end_time}")
    await _render_schedule(call, barber["id"], lang)


@router.callback_query(F.data.startswith("set_day_off_wh_"))
async def set_day_off(call: types.CallbackQuery, state: FSMContext):
    await _apply_day_preset(call, state, "00:00", "00:00")


@router.callback_query(F.data.startswith("set_day_std_wh_"))
async def set_day_std(call: types.CallbackQuery, state: FSMContext):
    await _apply_day_preset(call, state, "10:00", "20:00")


@router.callback_query(F.data.startswith("set_day_24h_wh_"))
async def set_day_24h(call: types.CallbackQuery, state: FSMContext):
    await _apply_day_preset(call, state, "00:00", "23:59")


async def _apply_day_preset(call: types.CallbackQuery, state: FSMContext, start_time: str, end_time: str):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    wh_id = int(call.data.split("_")[4])
    lang = (await state.get_data()).get("lang", "uz")
    wh = get_work_hour_by_id(wh_id)
    barber = get_barber(wh["barber_id"], shop_id) if wh else None
    if not wh or not barber:
        await call.answer("Jadval topilmadi." if lang == "uz" else "График не найден.", show_alert=True)
        return

    try:
        update_day_schedule(wh["barber_id"], wh["dow"], start_time, end_time)
    except ValueError as exc:
        await call.answer(str(exc), show_alert=True)
        return

    await call.answer(f"{start_time}-{end_time}")
    await _render_schedule(call, barber["id"], lang)


@router.callback_query(F.data == "admin_share_link")
async def admin_share_link(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    shop = get_shop(shop_id)
    if not shop:
        await call.answer("Do'kon topilmadi." if lang == "uz" else "Салон не найден.", show_alert=True)
        return

    bot_username = (await call.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=shopcode_{shop['public_code']}"
    text = (
        f"<b>Bron havolasi</b>\n\nDo'kon: <b>{shop['name']}</b>\nHavola: {link}\n\nUni mijozlarga yuboring yoki QR qilib chop eting."
        if lang == "uz"
        else
        f"<b>Ссылка для записи</b>\n\nСалон: <b>{shop['name']}</b>\nСсылка: {link}\n\nОтправьте её клиентам или распечатайте как QR."
    )
    await safe_edit_text(call.message, text, callback=call, reply_markup=admin_share_keyboard(lang=lang), parse_mode="HTML")


@router.callback_query(F.data == "admin_help")
async def admin_help(call: types.CallbackQuery, state: FSMContext):
    shop_id = await require_owner_shop(call, state)
    if not shop_id:
        return

    lang = (await state.get_data()).get("lang", "uz")
    await safe_edit_text(
        call.message,
        get_admin_help_text(lang),
        callback=call,
        reply_markup=admin_share_keyboard(lang=lang),
        parse_mode="HTML",
    )
