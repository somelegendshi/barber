import os

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from app.bot.handlers_super_admin import boss_main_keyboard
from app.bot.help_content import get_admin_help_text, get_customer_help_text
from app.bot.keyboards import (
    admin_menu_keyboard,
    customer_settings_keyboard,
    lang_keyboard,
    main_menu_keyboard,
    services_keyboard,
)
from app.bot.messages import WELCOME_MSG, get_msg
from app.bot.ui import safe_edit_text
from app.db.repository import (
    ensure_customer,
    get_admin_shop_id,
    get_customer_language,
    get_shop,
    list_services,
    resolve_shop_reference,
    set_customer_language,
)
from app.utils.text import resolve_lang

router = Router()

LANGUAGE_PROMPT = "Tilni tanlang / Выберите язык:"


def is_super_admin(user_id: int) -> bool:
    owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    return str(user_id) in [oid.strip() for oid in owner_ids if oid.strip()]


def user_is_admin(user_id: int, state_data: dict) -> bool:
    return bool(get_admin_shop_id(user_id) or state_data.get("is_admin") or is_super_admin(user_id))


def _has_explicit_customer_language(state_data: dict, saved_lang: str | None) -> bool:
    return bool(saved_lang or state_data.get("lang_confirmed"))


def _language_saved_text(lang: str) -> str:
    return "Til saqlandi." if lang == "uz" else "Язык сохранён."


async def _ask_customer_language(message: types.Message, state: FSMContext, shop: dict):
    await state.update_data(active_shop_id=shop["id"], is_admin=False)
    welcome_text = (
        f"{LANGUAGE_PROMPT}\n\n"
        f"{WELCOME_MSG.format(name=message.from_user.full_name)}\n\n"
        f"<b>{shop['name']}</b>"
    )
    image_url = "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?q=80&w=1000&auto=format&fit=crop"

    try:
        await message.answer_photo(
            photo=image_url,
            caption=welcome_text,
            reply_markup=lang_keyboard(),
            parse_mode="HTML",
        )
    except Exception:
        await message.answer(welcome_text, reply_markup=lang_keyboard(), parse_mode="HTML")


async def _show_menu_after_language_choice(call: types.CallbackQuery, state: FSMContext, lang: str):
    data = await state.get_data()
    user_id = call.from_user.id
    admin_shop_id = get_admin_shop_id(user_id)

    if admin_shop_id:
        shop = get_shop(admin_shop_id)
        shop_name = shop["name"] if shop else f"Shop {admin_shop_id}"
        await state.update_data(active_shop_id=admin_shop_id, is_admin=True, lang=lang, lang_confirmed=True)
        await call.message.answer(
            f"{_language_saved_text(lang)}\n\nAdmin: <b>{shop_name}</b>",
            reply_markup=admin_menu_keyboard(lang=lang),
            parse_mode="HTML",
        )
        return

    shop_id = data.get("active_shop_id")
    shop = get_shop(shop_id) if shop_id else None
    if shop:
        await state.update_data(active_shop_id=shop_id, is_admin=False, lang=lang, lang_confirmed=True)
        await call.message.answer(
            f"{_language_saved_text(lang)}\n\n<b>{shop['name']}</b>",
            reply_markup=main_menu_keyboard(lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(lang=lang, lang_confirmed=True, is_admin=False)
    await call.message.answer(
        (
            "Til saqlandi.\n\nBron qilish uchun salon havolasi orqali kiring."
            if lang == "uz"
            else
            "Язык сохранён.\n\nДля записи откройте ссылку салона."
        ),
        reply_markup=types.ReplyKeyboardRemove(),
    )


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    args = message.text.split()
    data = await state.get_data()
    saved_lang = get_customer_language(user_id)
    lang = resolve_lang(data.get("lang"), saved_lang, telegram_lang=message.from_user.language_code)
    has_shop_start_arg = len(args) > 1 and args[1].startswith(("shopcode_", "shop_"))

    shop_managed_by_user = get_admin_shop_id(user_id)
    if shop_managed_by_user:
        await state.update_data(active_shop_id=shop_managed_by_user, is_admin=True, lang=lang)
        shop = get_shop(shop_managed_by_user)
        shop_name = shop["name"] if shop else f"Shop {shop_managed_by_user}"
        text = (
            f"Salom, {message.from_user.full_name}!\nSiz <b>{shop_name}</b> uchun admin sifatida kirdingiz."
            if lang == "uz"
            else
            f"Здравствуйте, {message.from_user.full_name}!\nВы вошли как админ салона <b>{shop_name}</b>."
        )
        await message.answer(text, reply_markup=admin_menu_keyboard(lang=lang), parse_mode="HTML")
        return

    shop_id = None
    shop = None
    if len(args) > 1:
        start_arg = args[1]
        try:
            if start_arg.startswith("shopcode_"):
                shop = resolve_shop_reference(int(start_arg.split("_")[1]))
                shop_id = shop["id"] if shop else None
            elif start_arg.startswith("shop_"):
                shop_id = int(start_arg.split("_")[1])
                shop = get_shop(shop_id)
        except ValueError:
            shop_id = None
            shop = None

    if not shop_id:
        shop_id = data.get("active_shop_id")
        if shop_id:
            shop = get_shop(shop_id)

    if is_super_admin(user_id):
        if not shop_id:
            await state.update_data(lang=lang)
            await message.answer(
                "<b>Super Admin Panel</b>\n\nDo'kon tanlash uchun /boss menyusidan foydalaning."
                if lang == "uz"
                else
                "<b>Панель супер-админа</b>\n\nДля выбора салона используйте меню /boss.",
                reply_markup=boss_main_keyboard(lang=lang),
                parse_mode="HTML",
            )
            return

        shop = shop or get_shop(shop_id)
        if not shop:
            await message.answer("Shop topilmadi." if lang == "uz" else "Салон не найден.")
            return

        await state.update_data(active_shop_id=shop_id, is_admin=True, lang=lang)
        await message.answer(
            f"Super admin rejimi.\nTanlangan do'kon: <b>{shop['name']}</b>"
            if lang == "uz"
            else
            f"Режим супер-админа.\nВыбран салон: <b>{shop['name']}</b>",
            reply_markup=admin_menu_keyboard(lang=lang),
            parse_mode="HTML",
        )
        return

    if not shop_id:
        await message.answer(
            "Botga shop havolasi orqali kiring.\nMasalan: <code>t.me/barber_bot?start=shopcode_1</code>"
            if lang == "uz"
            else
            "Откройте бота по ссылке салона.\nНапример: <code>t.me/barber_bot?start=shopcode_1</code>",
            parse_mode="HTML",
        )
        return

    shop = shop or get_shop(shop_id)
    if not shop:
        await message.answer(
            "Do'kon topilmadi. Havola eskirgan bo'lishi mumkin."
            if lang == "uz"
            else
            "Салон не найден. Возможно, ссылка устарела.",
            parse_mode="HTML",
        )
        return

    ensure_customer(
        user_id,
        message.from_user.full_name,
        username=message.from_user.username,
        language_code=saved_lang,
    )

    if saved_lang and not has_shop_start_arg:
        await state.update_data(active_shop_id=shop_id, is_admin=False, lang=saved_lang, lang_confirmed=True)
        text = (
            f"👋 Xush kelibsiz, <b>{message.from_user.full_name}</b>!\n\n"
            f"<b>{shop['name']}</b>\n\n"
            "Xizmatni tanlash uchun menyudan foydalaning."
            if saved_lang == "uz"
            else
            f"👋 Добро пожаловать, <b>{message.from_user.full_name}</b>!\n\n"
            f"<b>{shop['name']}</b>\n\n"
            "Выберите нужный раздел в меню."
        )
        await message.answer(text, reply_markup=main_menu_keyboard(lang=saved_lang), parse_mode="HTML")
        return

    await _ask_customer_language(message, state, shop)


@router.message(Command("help"))
async def cmd_help(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = resolve_lang(
        data.get("lang"),
        get_customer_language(message.from_user.id),
        telegram_lang=message.from_user.language_code,
    )
    await state.update_data(lang=lang)
    text = get_admin_help_text(lang) if user_is_admin(message.from_user.id, data) else get_customer_help_text(lang)
    await message.answer(text, parse_mode="HTML")


@router.message(Command("language"))
async def cmd_language(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = resolve_lang(
        data.get("lang"),
        get_customer_language(message.from_user.id),
        telegram_lang=message.from_user.language_code,
    )
    await state.update_data(lang=lang)
    await message.answer(LANGUAGE_PROMPT, reply_markup=lang_keyboard())


@router.callback_query(F.data.startswith("lang_"))
async def set_lang(call: types.CallbackQuery, state: FSMContext):
    lang_code = call.data.split("_")[1]
    if lang_code not in {"uz", "ru"}:
        await call.answer("Unsupported language.", show_alert=True)
        return

    await state.update_data(lang=lang_code, lang_confirmed=True)
    set_customer_language(
        call.from_user.id,
        call.from_user.full_name,
        lang_code,
        username=call.from_user.username,
    )
    try:
        await call.message.delete()
    except Exception:
        pass
    await _show_menu_after_language_choice(call, state, lang_code)
    await call.answer()


@router.message(F.text == "✂️ Xizmatga yozilish")
@router.message(F.text == "✂️ Записаться на услугу")
@router.message(F.text == "Xizmatga yozilish")
@router.message(F.text == "Записаться на услугу")
async def handle_new_booking(message: types.Message, state: FSMContext):
    data = await state.get_data()
    saved_lang = get_customer_language(message.from_user.id)
    if not _has_explicit_customer_language(data, saved_lang):
        await message.answer(LANGUAGE_PROMPT, reply_markup=lang_keyboard())
        return

    lang = resolve_lang(
        data.get("lang"),
        saved_lang,
        telegram_lang=message.from_user.language_code,
    )
    await state.update_data(lang=lang)
    shop_id = data.get("active_shop_id")

    if not shop_id:
        await message.answer("Session tugadi. Shop havolasidan qayta kiring." if lang == "uz" else "Сессия завершена. Откройте ссылку салона заново.")
        return

    shop = get_shop(shop_id)
    if not shop:
        await message.answer("Shop ma'lumotini o'qib bo'lmadi." if lang == "uz" else "Не удалось загрузить данные салона.")
        return

    services = list_services(shop_id=shop_id)
    if not services:
        await message.answer("Xizmatlar topilmadi." if lang == "uz" else "Услуги не найдены.")
        return

    await message.answer(get_msg("select_service", lang=lang), reply_markup=services_keyboard(services, lang=lang), parse_mode="HTML")


@router.message(F.text == "📅 Mening buyurtmalarim")
@router.message(F.text == "📅 Мои записи")
@router.message(F.text == "Mening buyurtmalarim")
@router.message(F.text == "Мои записи")
async def handle_my_bookings(message: types.Message, state: FSMContext):
    from app.bot.handlers_customer import cmd_my_bookings

    await cmd_my_bookings(message, state)


@router.message(F.text == "⚙️ Sozlamalar")
@router.message(F.text == "⚙️ Настройки")
@router.message(F.text == "Sozlamalar")
@router.message(F.text == "Настройки")
async def handle_settings(message: types.Message, state: FSMContext):
    data = await state.get_data()
    saved_lang = get_customer_language(message.from_user.id)
    if not _has_explicit_customer_language(data, saved_lang):
        await message.answer(LANGUAGE_PROMPT, reply_markup=lang_keyboard())
        return

    lang = resolve_lang(
        data.get("lang"),
        saved_lang,
        telegram_lang=message.from_user.language_code,
    )
    await state.update_data(lang=lang)
    text = "Sozlamalar" if lang == "uz" else "Настройки"
    await message.answer(text, reply_markup=customer_settings_keyboard(lang=lang))


@router.callback_query(F.data == "settings_language")
async def customer_settings_language(call: types.CallbackQuery):
    await safe_edit_text(
        call.message,
        LANGUAGE_PROMPT,
        callback=call,
        reply_markup=lang_keyboard(),
    )


@router.callback_query(F.data == "settings_help")
async def customer_settings_help(call: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("lang", "uz")
    await safe_edit_text(
        call.message,
        get_customer_help_text(lang),
        callback=call,
        reply_markup=customer_settings_keyboard(lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "close_customer_settings")
async def close_customer_settings(call: types.CallbackQuery):
    await call.message.delete()
