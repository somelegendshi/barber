from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from app.db.repository import ensure_customer, list_services, get_shop
from app.bot.keyboards import services_keyboard, lang_keyboard, main_menu_keyboard, admin_menu_keyboard, admin_settings_keyboard
from app.bot.messages import WELCOME_MSG, get_msg
from app.bot.handlers_owner import is_owner
import os

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # Get args (e.g., /start shop_1)
    args = message.text.split()
    shop_id = 1 # Default fallback
    
    if len(args) > 1 and args[1].startswith("shop_"):
        try:
            shop_id = int(args[1].split("_")[1])
        except ValueError:
            pass
            
    # Save shop_id to state
    await state.update_data(active_shop_id=shop_id)
    
    # Ensure customer is registered
    user_id = message.from_user.id
    name = message.from_user.full_name
    username = message.from_user.username
    ensure_customer(user_id, name, username=username)
    
    # Check permissions
    if is_owner(user_id):
         await message.answer(
             f"👋 Salom, Xo'jayin! (Admin Panel - Shop {shop_id})\n"
             f"Siz admin sifatida kirdingiz.",
             reply_markup=admin_menu_keyboard()
         )
         return
    
    # Verify Shop Exists
    shop = get_shop(shop_id)
    if not shop:
        await message.answer("⚠️ Shop not found. Defaulting to Main Shop.")
        shop_id = 1
        shop = get_shop(1)
        await state.update_data(active_shop_id=1)

    # Send welcome WITH PHOTO
    shop_name = shop['name'] if shop else "Top Barber"
    welcome_text = WELCOME_MSG.format(name=name) + f"\n\n📍 <b>{shop_name}</b>"
    
    image_url = "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?q=80&w=1000&auto=format&fit=crop"
    
    await message.answer_photo(
        photo=image_url,
        caption=welcome_text,
        reply_markup=lang_keyboard()
    )

@router.callback_query(F.data.startswith("lang_"))
async def set_lang(call: types.CallbackQuery, state: FSMContext):
    lang_code = call.data.split("_")[1]
    await state.update_data(lang=lang_code)
    
    # Send Main Menu
    menu_text = "🏠 Asosiy menyu" if lang_code == "uz" else "🏠 Главное меню"
    
    # Delete the previous inline keyboard message (language selection)
    await call.message.delete()
    
    await call.message.answer(menu_text, reply_markup=main_menu_keyboard(lang=lang_code))

# --- MAIN MENU HANDLERS ---

@router.message(F.text == "✂️ Xizmatga yozilish")
@router.message(F.text == "✂️ Записаться на услугу")
async def handle_new_booking(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id", 1)
    
    services = list_services(shop_id=shop_id)
    
    if not services:
        msg_empty = "⚠️ Xizmatlar topilmadi." if lang == "uz" else "⚠️ Услуги не найдены."
        await message.answer(msg_empty)
        return
        
    msg_text = get_msg("select_service", lang=lang)
    await message.answer(msg_text, reply_markup=services_keyboard(services, lang=lang))

@router.message(F.text == "📅 Mening buyurtmalarim")
@router.message(F.text == "📅 Мои записи")
async def handle_my_bookings(message: types.Message, state: FSMContext):
    from app.bot.handlers_customer import cmd_my_bookings
    await cmd_my_bookings(message, state)

@router.message(F.text == "📞 Biz bilan aloqa")
@router.message(F.text == "📞 Контакты")
async def handle_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id", 1)
    shop = get_shop(shop_id)
    shop_name = shop['name'] if shop else "Bizning Sartaroshxona"
    
    contact_text = (
        f"📍 <b>{shop_name}</b>\n"
        "📞 <b>Tel:</b> +998 90 123 45 67\n"
        "🕒 <b>Ish vaqti:</b> 09:00 - 21:00"
    ) if lang == "uz" else (
        f"📍 <b>{shop_name}</b>\n"
        "📞 <b>Тел:</b> +998 90 123 45 67\n"
        "🕒 <b>Режим работы:</b> 09:00 - 21:00"
    )
    await message.answer(contact_text)

# --- SETTINGS MENU ---

@router.message(F.text == "⚙️ Sozlamalar")
@router.message(F.text == "⚙️ Настройки")
async def handle_settings(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = "⚙️ Sozlamalar bo'limi" if lang == "uz" else "⚙️ Раздел настроек"
    # FIXED: Using the correct imported name
    await message.answer(text, reply_markup=admin_settings_keyboard(lang=lang))

@router.message(F.text == "🌐 Tilni o'zgartirish")
@router.message(F.text == "🌐 Сменить язык")
async def handle_change_lang(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = "🌐 Tilni tanlang:" if lang == "uz" else "🌐 Выберите язык:"
    
    # Show inline keyboard again
    await message.answer(text, reply_markup=lang_keyboard())

@router.message(F.text == "⬅️ Orqaga")
@router.message(F.text == "⬅️ Назад")
async def handle_back_to_main(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = "🏠 Asosiy menyu" if lang == "uz" else "🏠 Главное меню"
    await message.answer(text, reply_markup=main_menu_keyboard(lang=lang))
