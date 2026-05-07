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
    assign_shop_admin,
    create_default_shop_services,
    create_shop_db,
    delete_shop_db,
    get_shop,
    list_shop_admin_ids,
    list_shops,
    sync_core_id_sequences,
)
from app.utils.text import resolve_lang

router = Router()


class BossStates(StatesGroup):
    WAITING_SHOP_NAME = State()
    WAITING_FIRST_BARBER_NAME = State()
    WAITING_SHOP_ADMIN = State()


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
        cur.execute("SELECT id, display_name, notify_telegram_id FROM barbers WHERE shop_id = %s ORDER BY id", (shop_id,))
        barbers = cur.fetchall()
    admin_ids = list_shop_admin_ids(shop_id)

    text = (
        f"🏢 <b>Do'kon ma'lumotlari</b>\n\n📌 ID: {shop['public_code']}\n"
        f"🧩 DB ID: {shop['id']}\n📝 Nom: {shop['name']}\n\n💈 <b>Ustalar:</b>\n"
        if lang == "uz"
        else
        f"🏢 <b>Информация о салоне</b>\n\n📌 ID: {shop['public_code']}\n"
        f"🧩 DB ID: {shop['id']}\n📝 Название: {shop['name']}\n\n💈 <b>Мастера:</b>\n"
    )
    for barber in barbers:
        tg_info = f" (Notify ID: <code>{barber['notify_telegram_id']}</code>)" if barber["notify_telegram_id"] else ""
        text += f"• {barber['display_name']} [ID:{barber['id']}] {tg_info}\n"

    text += "\nAdmins:\n"
    if admin_ids:
        for admin_id in admin_ids:
            text += f"- <code>{admin_id}</code>\n"
    else:
        text += "- not assigned\n"

    bot_username = (await call.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=shopcode_{shop['public_code']}"
    text += f"\n🔗 {link}"

    back_text = "🔙 Ro'yxatga qaytish" if lang == "uz" else "🔙 Назад к списку"
    open_text = "⚡ Admin panelni ochish" if lang == "uz" else "⚡ Открыть админ-панель"
    delete_text = "🗑 Do'konni o'chirish" if lang == "uz" else "🗑 Удалить салон"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=open_text, callback_data=f"boss_use_shop_{shop_id}")],
            [InlineKeyboardButton(text=delete_text, callback_data=f"boss_delete_shop_{shop_id}")],
            [InlineKeyboardButton(text=back_text, callback_data="boss_list_shops")],
        ]
    )

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("boss_delete_shop_"))
async def cb_boss_delete_shop(call: types.CallbackQuery, state: FSMContext):
    if not is_super_admin(call.from_user.id):
        return

    shop_id = int(call.data.split("_")[3])
    shop = get_shop(shop_id)
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), call.from_user.language_code)
    if not shop:
        await call.answer("Topilmadi" if lang == "uz" else "Не найдено", show_alert=True)
        return

    confirm_text = "Ha, o'chirish" if lang == "uz" else "Да, удалить"
    cancel_text = "Bekor qilish" if lang == "uz" else "Отмена"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=confirm_text, callback_data=f"boss_confirm_delete_shop_{shop_id}")],
            [InlineKeyboardButton(text=cancel_text, callback_data=f"boss_shop_{shop_id}")],
        ]
    )
    await call.message.edit_text(
        (
            f"⚠️ <b>Do'konni o'chirishni tasdiqlang</b>\n\n"
            f"Do'kon: <b>{shop['name']}</b>\n"
            f"ID: <code>{shop['public_code']}</code>\n\n"
            "Bu amal barcha ustalar, xizmatlar, ish vaqtlari va buyurtmalarni o'chiradi."
            if lang == "uz"
            else
            f"⚠️ <b>Подтвердите удаление салона</b>\n\n"
            f"Салон: <b>{shop['name']}</b>\n"
            f"ID: <code>{shop['public_code']}</code>\n\n"
            "Это удалит всех мастеров, услуги, графики и записи."
        ),
        reply_markup=kb,
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("boss_confirm_delete_shop_"))
async def cb_boss_confirm_delete_shop(call: types.CallbackQuery, state: FSMContext):
    if not is_super_admin(call.from_user.id):
        return

    shop_id = int(call.data.split("_")[4])
    shop = get_shop(shop_id)
    data = await state.get_data()
    lang = resolve_lang(data.get("lang"), call.from_user.language_code)
    if not shop:
        await call.answer("Topilmadi" if lang == "uz" else "Не найдено", show_alert=True)
        return

    deleted = delete_shop_db(shop_id)
    if deleted:
        await state.update_data(active_shop_id=None, is_admin=False, lang=lang)
        sync_core_id_sequences()
        await call.message.edit_text(
            f"✅ Do'kon o'chirildi: <b>{shop['name']}</b>"
            if lang == "uz"
            else
            f"✅ Салон удалён: <b>{shop['name']}</b>",
            reply_markup=boss_main_keyboard(lang=lang),
            parse_mode="HTML",
        )
    else:
        await call.answer("O'chirilmadi." if lang == "uz" else "Не удалено.", show_alert=True)


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
            assign_shop_admin(shop_id, admin_id)

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
