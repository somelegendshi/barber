from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from app.db.repository import ensure_customer, list_services, get_shop, get_admin_shop_id
from app.bot.keyboards import services_keyboard, lang_keyboard, main_menu_keyboard, admin_menu_keyboard, admin_settings_keyboard
from app.bot.messages import WELCOME_MSG, get_msg
import os

router = Router()

def is_super_admin(user_id: int) -> bool:
    owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    return str(user_id) in [oid.strip() for oid in owner_ids]

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    args = message.text.split()
    
    # 1. Check if user is a BARBER/ADMIN FIRST
    shop_managed_by_user = get_admin_shop_id(user_id)
    
    if shop_managed_by_user:
        await state.update_data(active_shop_id=shop_managed_by_user, is_admin=True)
        shop = get_shop(shop_managed_by_user)
        shop_name = shop['name'] if shop else f"Shop {shop_managed_by_user}"
        
        await message.answer(
            f"👋 Salom, {message.from_user.full_name}!\n"
            f"Siz <b>{shop_name}</b> boshqaruvchisi sifatida kirdingiz.\n"
            f"<i>Tizim holati: ✅ Faol (Active)</i>",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    # 2. Extract Shop ID from Deep Link
    shop_id = None
    if len(args) > 1 and args[1].startswith("shop_"):
        try: 
            shop_id = int(args[1].split("_")[1])
        except: 
            pass

    # 3. Fallback: Check existing session state
    if not shop_id:
        data = await state.get_data()
        shop_id = data.get("active_shop_id")

    # 4. Super Admin Override (Default to Shop 1 if no deep link)
    if is_super_admin(user_id):
        if not shop_id:
            shop_id = 1 # Default for admin testing
        
        shop = get_shop(shop_id)
        if not shop:
             await message.answer(f"⚠️ Admin Warning: Shop {shop_id} not found.")
             return

        await state.update_data(active_shop_id=shop_id, is_admin=True)
        await message.answer(
            f"⚡ Salom, Boss! (Super Admin)\nBoshqarilayotgan do'kon: <b>{shop['name']}</b>",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    # 5. Regular User - MUST have a valid shop_id
    if not shop_id:
        await message.answer(
            "⚠️ <b>Xatolik / Ошибка</b>\n\n"
            "Iltimos, botga do'kon havolasi orqali kiring.\n"
            "Masalan: <code>t.me/barber_bot?start=shop_1</code>\n\n"
            "<i>Пожалуйста, используйте ссылку магазина для входа.</i>",
            parse_mode="HTML"
        )
        return

    # 6. Validate Shop
    shop = get_shop(shop_id)
    if not shop:
        await message.answer(
            "😔 <b>Do'kon topilmadi / Магазин не найден</b>\n\n"
            "Ushbu havola eskirgan yoki noto'g'ri.\n"
            "<i>Ссылка недействительна.</i>",
            parse_mode="HTML"
        )
        return

    # 7. Success - Update State & Welcome
    await state.update_data(active_shop_id=shop_id, is_admin=False)
    ensure_customer(user_id, message.from_user.full_name, username=message.from_user.username)
    
    welcome_text = WELCOME_MSG.format(name=message.from_user.full_name) + f"\n\n📍 <b>{shop['name']}</b>"
    # Note: Hardcoded image for now, ideally this comes from shop DB
    image_url = "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?q=80&w=1000&auto=format&fit=crop"
    
    await message.answer_photo(
        photo=image_url,
        caption=welcome_text,
        reply_markup=lang_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("lang_"))
async def set_lang(call: types.CallbackQuery, state: FSMContext):
    lang_code = call.data.split("_")[1]
    await state.update_data(lang=lang_code)
    # Re-fetch data for dynamic localized menu
    data = await state.get_data() 
    
    menu_text = "🏠 Asosiy menyu" if lang_code == "uz" else "🏠 Главное меню"
    await call.message.delete()
    await call.message.answer(menu_text, reply_markup=main_menu_keyboard(lang=lang_code))

@router.message(F.text == "✂️ Xizmatga yozilish")
@router.message(F.text == "✂️ Записаться на услугу")
async def handle_new_booking(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id")
    
    if not shop_id:
        await message.answer("⚠️ Session expired. Please restart via shop link.")
        return
    
    shop = get_shop(shop_id)
    if not shop:
        await message.answer("⚠️ Shop data error.")
        return

    services = list_services(shop_id=shop_id)
    if not services:
        msg = "⚠️ Xizmatlar topilmadi." if lang=="uz" else "⚠️ Услуги не найдены."
        await message.answer(msg)
        return
    
    await message.answer(get_msg("select_service", lang=lang), reply_markup=services_keyboard(services, lang=lang))

@router.message(F.text == "📅 Mening buyurtmalarim")
@router.message(F.text == "📅 Мои записи")
async def handle_my_bookings(message: types.Message, state: FSMContext):
    from app.bot.handlers_customer import cmd_my_bookings
    await cmd_my_bookings(message, state)

@router.message(F.text == "⚙️ Sozlamalar")
@router.message(F.text == "⚙️ Настройки")
async def handle_settings(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await message.answer("⚙️ Sozlamalar", reply_markup=admin_settings_keyboard(lang=lang))
