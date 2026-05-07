import os

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards import admin_menu_keyboard
from app.db.conn import get_db
from app.db.repository import (
    add_barber_db,
    assign_barber_telegram_id,
    create_default_shop_services,
    create_shop_db,
    get_shop,
    list_shops,
)
from app.utils.text import resolve_lang

router = Router()


class BossStates(StatesGroup):
    WAITING_SHOP_NAME = State()
    WAITING_FIRST_BARBER_NAME = State()
    WAITING_SHOP_ADMIN = State()
    WAITING_ADMIN_ASSIGNMENT = State()


def is_super_admin(user_id: int) -> bool:
    ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    return str(user_id) in [value.strip() for value in ids if value.strip()]


def boss_main_keyboard(lang: str = "uz"):
    rows = (
        [
            [InlineKeyboardButton(text="🏢 Do'konlar ro'yxati", callback_data="boss_list_shops")],
            [InlineKeyboardButton(text="➕ Yangi do'kon yaratish", callback_data="boss_add_shop")],
            [InlineKeyboardButton(text="❌ Yopish", callback_data="boss_close")],
        ]
        if lang == "uz"
        else
        [
            [InlineKeyboardButton(text="🏢 Список салонов", callback_data="boss_list_shops")],
            [InlineKeyboardButton(text="➕ Создать новый салон", callback_data="boss_add_shop")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="boss_close")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def boss_shops_keyboard(shops, lang: str = "uz"):
    rows = []
    for shop in shops:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"💈 {shop['name']} (ID:{shop['public_code']})",
                    callback_data=f"boss_shop_{shop['id']}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="🔙 Orqaga" if lang == "uz" else "🔙 Назад", callback_data="boss_home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("boss"))
async def cmd_boss(message: types.Message, state: FSMContext):
    if not is_super_admin(message.from_user.id):
        return

    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), message.from_user.language_code)
    await state.update_data(lang=lang)
    await message.answer(
        "🧑‍💼 <b>Super-admin menyusi</b>\n\nQuyidagilardan birini tanlang:"
        if lang == "uz"
        else
        "🧑‍💼 <b>Меню супер-админа</b>\n\nВыберите действие:",
        reply_markup=boss_main_keyboard(lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "boss_home")
async def cb_boss_home(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), call.from_user.language_code)
    await state.clear()
    await state.update_data(lang=lang)
    await call.message.edit_text(
        "🧑‍💼 <b>Super-admin menyusi</b>\n\nQuyidagilardan birini tanlang:"
        if lang == "uz"
        else
        "🧑‍💼 <b>Меню супер-админа</b>\n\nВыберите действие:",
        reply_markup=boss_main_keyboard(lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "boss_close")
async def cb_boss_close(call: types.CallbackQuery):
    await call.message.delete()


@router.callback_query(F.data == "boss_list_shops")
async def cb_boss_list_shops(call: types.CallbackQuery, state: FSMContext):
    shops = list_shops()
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), call.from_user.language_code)
    if not shops:
        await call.answer("Do'konlar topilmadi!" if lang == "uz" else "Салоны не найдены!", show_alert=True)
        return

    await call.message.edit_text(
        "🏢 <b>Barcha do'konlar</b>" if lang == "uz" else "🏢 <b>Все салоны</b>",
        reply_markup=boss_shops_keyboard(shops, lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("boss_shop_"))
async def cb_boss_shop_info(call: types.CallbackQuery, state: FSMContext):
    shop_id = int(call.data.split("_")[2])
    shop = get_shop(shop_id)
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), call.from_user.language_code)
    if not shop:
        await call.answer("Topilmadi" if lang == "uz" else "Не найдено", show_alert=True)
        return

    with get_db() as cur:
        cur.execute("SELECT id, display_name, telegram_id FROM barbers WHERE shop_id = %s ORDER BY id", (shop_id,))
        barbers = cur.fetchall()

    text = (
        f"🏢 <b>Do'kon ma'lumotlari</b>\n\n📌 ID: {shop['public_code']}\n"
        f"🧩 DB ID: {shop['id']}\n📝 Nom: {shop['name']}\n\n💈 <b>Ustalar:</b>\n"
        if lang == "uz"
        else
        f"🏢 <b>Информация о салоне</b>\n\n📌 ID: {shop['public_code']}\n"
        f"🧩 DB ID: {shop['id']}\n📝 Название: {shop['name']}\n\n💈 <b>Мастера:</b>\n"
    )
    for barber in barbers:
        tg_info = f" (TG ID: <code>{barber['telegram_id']}</code>)" if barber["telegram_id"] else ""
        text += f"• {barber['display_name']} [ID:{barber['id']}] {tg_info}\n"

    bot_username = (await call.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=shopcode_{shop['public_code']}"
    text += f"\n🔗 {link}"

    back_text = "🔙 Ro'yxatga qaytish" if lang == "uz" else "🔙 Назад к списку"
    open_text = "⚡ Admin panelni ochish" if lang == "uz" else "⚡ Открыть админ-панель"
    assign_text = "🔐 Admin ID biriktirish" if lang == "uz" else "🔐 Привязать ID админа"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=open_text, callback_data=f"boss_use_shop_{shop_id}")],
            [InlineKeyboardButton(text=assign_text, callback_data=f"boss_assign_admin_{shop_id}")],
            [InlineKeyboardButton(text=back_text, callback_data="boss_list_shops")],
        ]
    )

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("boss_use_shop_"))
async def cb_boss_use_shop(call: types.CallbackQuery, state: FSMContext):
    shop_id = int(call.data.split("_")[3])
    shop = get_shop(shop_id)
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), call.from_user.language_code)
    if not shop:
        await call.answer("Topilmadi" if lang == "uz" else "Не найдено", show_alert=True)
        return

    await state.update_data(active_shop_id=shop_id, is_admin=True, lang=lang)
    await call.message.edit_text(
        f"⚡ <b>{shop['name']}</b> admin paneli ochildi."
        if lang == "uz"
        else
        f"⚡ Открыта админ-панель салона <b>{shop['name']}</b>.",
        parse_mode="HTML",
    )
    await call.message.answer(
        "Kerakli bo'limni tanlang:" if lang == "uz" else "Выберите нужный раздел:",
        reply_markup=admin_menu_keyboard(lang=lang),
    )
    await call.answer()


@router.callback_query(F.data.startswith("boss_assign_admin_"))
async def cb_boss_assign_admin_start(call: types.CallbackQuery, state: FSMContext):
    shop_id = int(call.data.split("_")[3])
    shop = get_shop(shop_id)
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), telegram_lang=call.from_user.language_code)
    if not shop:
        await call.answer("Topilmadi" if lang == "uz" else "Не найдено", show_alert=True)
        return

    with get_db() as cur:
        cur.execute(
            """
            SELECT id, display_name, telegram_id
            FROM barbers
            WHERE shop_id = %s AND is_active = TRUE
            ORDER BY id
            """,
            (shop_id,),
        )
        barbers = cur.fetchall()

    if not barbers:
        await call.answer(
            "Faol usta topilmadi." if lang == "uz" else "Активные мастера не найдены.",
            show_alert=True,
        )
        return

    rows = [
        (
            f"<b>{shop['name']}</b> uchun admin Telegram ID biriktirish.\n\n"
            "Format: <code>BARBER_ID TELEGRAM_ID</code>\n"
            "Masalan: <code>12 123456789</code>\n\n"
            "Usta o'z ID sini /my_id orqali oladi.\n\n"
            "<b>Ustalar:</b>"
        )
        if lang == "uz"
        else
        (
            f"Привязка Telegram ID админа для <b>{shop['name']}</b>.\n\n"
            "Формат: <code>BARBER_ID TELEGRAM_ID</code>\n"
            "Пример: <code>12 123456789</code>\n\n"
            "Мастер может получить ID через /my_id.\n\n"
            "<b>Мастера:</b>"
        )
    ]
    for barber in barbers:
        current_id = f" - TG: <code>{barber['telegram_id']}</code>" if barber.get("telegram_id") else ""
        rows.append(f"{barber['id']} - {barber['display_name']}{current_id}")

    await state.update_data(assign_admin_shop_id=shop_id, lang=lang)
    await call.message.edit_text("\n".join(rows), parse_mode="HTML")
    await state.set_state(BossStates.WAITING_ADMIN_ASSIGNMENT)
    await call.answer()


@router.message(BossStates.WAITING_ADMIN_ASSIGNMENT)
async def state_admin_assignment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), telegram_lang=message.from_user.language_code)
    shop_id = data.get("assign_admin_shop_id")
    if not shop_id:
        await state.clear()
        await state.update_data(lang=lang)
        await message.answer(
            "Session tugadi. /boss ni qayta oching."
            if lang == "uz"
            else "Сессия завершена. Откройте /boss заново."
        )
        return

    parts = (message.text or "").replace(",", " ").split()
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        await message.answer(
            "Format noto'g'ri. Masalan: 12 123456789"
            if lang == "uz"
            else "Неверный формат. Пример: 12 123456789"
        )
        return

    barber_id, telegram_id = map(int, parts)
    with get_db() as cur:
        cur.execute(
            """
            SELECT display_name
            FROM barbers
            WHERE id = %s AND shop_id = %s AND is_active = TRUE
            """,
            (barber_id, shop_id),
        )
        barber = cur.fetchone()

    if not barber:
        await message.answer(
            "Bu do'konda bunday faol usta yo'q."
            if lang == "uz"
            else "В этом салоне нет такого активного мастера."
        )
        return

    try:
        assign_barber_telegram_id(barber_id, telegram_id)
    except ValueError:
        await message.answer(
            "Bu Telegram ID boshqa ustaga biriktirilgan."
            if lang == "uz"
            else "Этот Telegram ID уже привязан к другому мастеру."
        )
        return

    shop = get_shop(shop_id)
    shop_name = shop["name"] if shop else f"Shop {shop_id}"
    await state.clear()
    await state.update_data(lang=lang)
    await message.answer(
        (
            f"✅ {barber['display_name']} endi <b>{shop_name}</b> admini.\n"
            f"Telegram ID: <code>{telegram_id}</code>"
        )
        if lang == "uz"
        else
        (
            f"✅ {barber['display_name']} теперь админ <b>{shop_name}</b>.\n"
            f"Telegram ID: <code>{telegram_id}</code>"
        ),
        parse_mode="HTML",
        reply_markup=boss_main_keyboard(lang=lang),
    )


@router.callback_query(F.data == "boss_add_shop")
async def cb_boss_add_shop(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), call.from_user.language_code)
    await call.message.edit_text(
        "➕ <b>Yangi do'kon nomini</b> kiriting:"
        if lang == "uz"
        else
        "➕ <b>Введите название нового салона</b>:",
        parse_mode="HTML",
    )
    await state.set_state(BossStates.WAITING_SHOP_NAME)


@router.message(BossStates.WAITING_SHOP_NAME)
async def state_shop_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), message.from_user.language_code)
    shop_name = (message.text or "").strip()
    if not shop_name:
        await message.answer("Nom bo'sh bo'lmasin." if lang == "uz" else "Название не должно быть пустым.")
        return

    await state.update_data(shop_name=shop_name, lang=lang)
    await message.answer(
        "Birinchi ustaning ismini kiriting:"
        if lang == "uz"
        else
        "Введите имя первого мастера:",
    )
    await state.set_state(BossStates.WAITING_FIRST_BARBER_NAME)


@router.message(BossStates.WAITING_FIRST_BARBER_NAME)
async def state_first_barber_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), message.from_user.language_code)
    barber_name = (message.text or "").strip()
    if not barber_name:
        await message.answer("Ism bo'sh bo'lmasin." if lang == "uz" else "Имя не должно быть пустым.")
        return

    await state.update_data(first_barber_name=barber_name, lang=lang)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="O'tkazib yuborish" if lang == "uz" else "Пропустить", callback_data="boss_skip_admin")]]
    )
    await message.answer(
        "Endi shop adminining Telegram ID sini kiriting.\nU /my_id yuborib ID sini olishi mumkin.\nYoki hozircha o'tkazib yuboring."
        if lang == "uz"
        else
        "Теперь введите Telegram ID администратора салона.\nОн может получить его через /my_id.\nИли пока пропустите.",
        reply_markup=kb,
    )
    await state.set_state(BossStates.WAITING_SHOP_ADMIN)


@router.callback_query(F.data == "boss_skip_admin")
async def cb_boss_skip_admin(call: types.CallbackQuery, state: FSMContext):
    await finish_shop_creation(call.message, state, None)
    await call.answer()


@router.message(BossStates.WAITING_SHOP_ADMIN)
async def state_shop_admin(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), message.from_user.language_code)
    if not (message.text or "").isdigit():
        await message.answer("Iltimos, faqat raqamlardan iborat Telegram ID kiriting." if lang == "uz" else "Введите Telegram ID только цифрами.")
        return

    await finish_shop_creation(message, state, int(message.text))


async def finish_shop_creation(message_or_call_msg, state: FSMContext, admin_id: int | None):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_name = data["shop_name"]
    first_barber_name = data["first_barber_name"]

    try:
        shop_id = create_shop_db(shop_name)
        create_default_shop_services(shop_id)
        barber_id = add_barber_db(shop_id, first_barber_name)
        shop = get_shop(shop_id)

        if admin_id:
            assign_barber_telegram_id(barber_id, admin_id)

        bot_username = (await message_or_call_msg.bot.get_me()).username
        public_code = shop["public_code"] if shop else shop_id
        link = f"https://t.me/{bot_username}?start=shopcode_{public_code}"

        text = (
            f"✅ <b>Yangi do'kon yaratildi!</b>\n\n"
            f"📌 Shop ID: <code>{public_code}</code>\n"
            f"📝 Nom: {shop_name}\n"
            f"💈 Birinchi usta: {first_barber_name}\n"
        ) if lang == "uz" else (
            f"✅ <b>Новый салон создан!</b>\n\n"
            f"📌 ID салона: <code>{public_code}</code>\n"
            f"📝 Название: {shop_name}\n"
            f"💈 Первый мастер: {first_barber_name}\n"
        )

        if admin_id:
            text += f"🔐 Admin TG ID: <code>{admin_id}</code>\n"
        else:
            text += "🔐 Admin TG ID: biriktirilmagan\n" if lang == "uz" else "🔐 Telegram ID админа: не привязан\n"

        text += (
            f"\n🔗 <b>Havola:</b>\n{link}\n\nEndi admin paneldan qolgan ustalarni qo'shishingiz mumkin."
            if lang == "uz"
            else
            f"\n🔗 <b>Ссылка:</b>\n{link}\n\nТеперь можно добавить остальных мастеров через админ-панель."
        )
        await message_or_call_msg.answer(text, parse_mode="HTML", reply_markup=boss_main_keyboard(lang=lang))
    except Exception as exc:
        await message_or_call_msg.answer(
            f"❌ Xatolik yuz berdi: {exc}" if lang == "uz" else f"❌ Произошла ошибка: {exc}",
            reply_markup=boss_main_keyboard(lang=lang),
        )

    await state.clear()
    await state.update_data(lang=lang)


@router.message(Command("my_id"))
async def cmd_my_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), message.from_user.language_code)
    await message.answer(
        f"Sizning ID: <code>{message.from_user.id}</code>\nBuni super-admin ga yuborishingiz mumkin."
        if lang == "uz"
        else
        f"Ваш ID: <code>{message.from_user.id}</code>\nЕго можно отправить супер-админу.",
        parse_mode="HTML",
    )
