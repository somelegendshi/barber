from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
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
    
    # 1. ARCHITECTURE FIX: Check if user is a BARBER/ADMIN FIRST
    # A barber should ALWAYS see their admin panel, regardless of which link they clicked.
    shop_managed_by_user = get_admin_shop_id(user_id)
    
    if shop_managed_by_user:
        # User is an Admin for this shop
        await state.update_data(active_shop_id=shop_managed_by_user, is_admin=True)
        shop = get_shop(shop_managed_by_user)
        shop_name = shop['name'] if shop else f"Shop {shop_managed_by_user}"
        
        await message.answer(
            f"👋 Salom, {message.from_user.full_name}!\n"
            f"Siz <b>{shop_name}</b> boshqaruvchisi sifatida kirdingiz.",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    # 2. If Super Admin (Boss)
    if is_super_admin(user_id):
        # Super admin can switch shops via links, but defaults to Shop 1
        shop_id = 1
        if len(args) > 1 and args[1].startswith("shop_"):
            try: shop_id = int(args[1].split("_")[1])
            except: pass
        
        await state.update_data(active_shop_id=shop_id, is_admin=True)
        await message.answer(
            f"⚡ Salom, Boss! (Super Admin)\nBoshqarilayotgan do'kon ID: {shop_id}",
            reply_markup=admin_menu_keyboard()
        )
        return

    # 3. Regular CLIENT Logic
    shop_id = 1
    if len(args) > 1 and args[1].startswith("shop_"):
        try: shop_id = int(args[1].split("_")[1])
        except: pass
    else:
        # Persist shop if they just type /start
        data = await state.get_data()
        shop_id = data.get("active_shop_id", 1)

    await state.update_data(active_shop_id=shop_id, is_admin=False)
    
    # Register customer
    ensure_customer(user_id, message.from_user.full_name, username=message.from_user.username)
    
    shop = get_shop(shop_id)
    shop_name = shop['name'] if shop else "BarberShop"
    
    welcome_text = WELCOME_MSG.format(name=message.from_user.full_name) + f"\n\n📍 <b>{shop_name}</b>"
    image_url = "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?q=80&w=1000&auto=format&fit=crop"
    
    await message.answer_photo(
        photo=image_url,
        caption=welcome_text,
        reply_markup=lang_keyboard(),
        parse_mode="HTML"
    )

# ... (rest of the file remains same, I'll rewrite the whole file to be safe)

@router.callback_query(F.data.startswith("lang_"))
async def set_lang(call: types.CallbackQuery, state: FSMContext):
    lang_code = call.data.split("_")[1]
    await state.update_data(lang=lang_code)
    menu_text = "🏠 Asosiy menyu" if lang_code == "uz" else "🏠 Главное меню"
    await call.message.delete()
    await call.message.answer(menu_text, reply_markup=main_menu_keyboard(lang=lang_code))

@router.message(F.text == "✂️ Xizmatga yozilish")
@router.message(F.text == "✂️ Записаться на услугу")
async def handle_new_booking(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id", 1)
    services = list_services(shop_id=shop_id)
    if not services:
        await message.answer("⚠️ Xizmatlar topilmadi.")
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
    # If admin, show settings. If customer, maybe show profile (currently just shows settings kb)
    await message.answer("⚙️ Settings", reply_markup=admin_settings_keyboard(lang=lang))
