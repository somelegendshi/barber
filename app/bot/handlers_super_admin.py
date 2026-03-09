from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

from app.db.repository import create_shop_db, add_barber_db, assign_barber_telegram_id, get_shop
from app.db.conn import get_db

router = Router()

class BossStates(StatesGroup):
    WAITING_SHOP_NAME = State()
    WAITING_SHOP_ADMIN = State()

def is_super_admin(user_id: int) -> bool:
    ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    return str(user_id) in [x.strip() for x in ids]

def get_all_shops():
    with get_db() as cur:
        cur.execute("SELECT id, name FROM shops ORDER BY id")
        return cur.fetchall()

def boss_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 Do'konlar ro'yxati", callback_data="boss_list_shops")],
        [InlineKeyboardButton(text="➕ Yangi Do'kon Yaratish", callback_data="boss_add_shop")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="boss_close")]
    ])

def boss_shops_keyboard(shops):
    kb = []
    for shop in shops:
        kb.append([InlineKeyboardButton(text=f"💈 {shop['name']} (ID:{shop['id']})", callback_data=f"boss_shop_{shop['id']}")])
    kb.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="boss_home")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(Command("boss"))
async def cmd_boss(message: types.Message):
    if not is_super_admin(message.from_user.id):
        return
    await message.answer("👑 <b>Super-Admin Menyusi</b>\n\nQuyidagilardan birini tanlang:", 
                         reply_markup=boss_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "boss_home")
async def cb_boss_home(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("👑 <b>Super-Admin Menyusi</b>\n\nQuyidagilardan birini tanlang:", 
                                 reply_markup=boss_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "boss_close")
async def cb_boss_close(call: types.CallbackQuery):
    await call.message.delete()

@router.callback_query(F.data == "boss_list_shops")
async def cb_boss_list_shops(call: types.CallbackQuery):
    shops = get_all_shops()
    if not shops:
        await call.answer("Do'konlar topilmadi!", show_alert=True)
        return
    await call.message.edit_text("🏢 <b>Barcha Do'konlar:</b>", reply_markup=boss_shops_keyboard(shops), parse_mode="HTML")

@router.callback_query(F.data.startswith("boss_shop_"))
async def cb_boss_shop_info(call: types.CallbackQuery):
    shop_id = int(call.data.split("_")[2])
    shop = get_shop(shop_id)
    if not shop:
        await call.answer("Topilmadi", show_alert=True)
        return
    
    with get_db() as cur:
        cur.execute("SELECT id, display_name, telegram_id FROM barbers WHERE shop_id = %s", (shop_id,))
        barbers = cur.fetchall()
        
    text = f"🏢 <b>Do'kon Ma'lumotlari</b>\n\n"
    text += f"🆔 ID: {shop['id']}\n"
    text += f"📛 Nom: {shop['name']}\n\n"
    text += f"💈 <b>Ustalar/Adminlar:</b>\n"
    for b in barbers:
        tg_info = f"(TG ID: <code>{b['telegram_id']}</code>)" if b['telegram_id'] else "(Biriktirilmagan)"
        text += f" - {b['display_name']} [ID:{b['id']}] {tg_info}\n"
    
    bot_username = (await call.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=shop_{shop['id']}"
    text += f"\n🔗 Bot Link:\n{link}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Ro'yxatga qaytish", callback_data="boss_list_shops")]
    ])
    
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

# Add Shop Flow
@router.callback_query(F.data == "boss_add_shop")
async def cb_boss_add_shop(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("➕ <b>Yangi Do'kon Nomi</b>ni kiriting:\n(Masalan: <i>Best Barbershop</i>)", parse_mode="HTML")
    await state.set_state(BossStates.WAITING_SHOP_NAME)

@router.message(BossStates.WAITING_SHOP_NAME)
async def state_shop_name(message: types.Message, state: FSMContext):
    shop_name = message.text.strip()
    await state.update_data(shop_name=shop_name)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'tkazib yuborish (Skip)", callback_data="boss_skip_admin")]
    ])
    await message.answer(f"✅ Nom qabul qilindi: <b>{shop_name}</b>\n\n"
                         f"🔑 Endi do'kon <b>Admini (Manager) ning Telegram ID</b> sini kiriting.\n"
                         f"ID ni bilish uchun u botga kirib /my_id yozishi mumkin.\n"
                         f"Yoki hozircha o'tkazib yuborishingiz mumkin.", reply_markup=kb, parse_mode="HTML")
    await state.set_state(BossStates.WAITING_SHOP_ADMIN)

@router.callback_query(F.data == "boss_skip_admin")
async def cb_boss_skip_admin(call: types.CallbackQuery, state: FSMContext):
    await finish_shop_creation(call.message, state, None)
    await call.answer()

@router.message(BossStates.WAITING_SHOP_ADMIN)
async def state_shop_admin(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Iltimos faqat raqamlardan iborat Telegram ID kiriting:")
        return
    await finish_shop_creation(message, state, int(message.text))

async def finish_shop_creation(message_or_call_msg, state: FSMContext, admin_id: int):
    data = await state.get_data()
    shop_name = data['shop_name']
    
    try:
        shop_id = create_shop_db(shop_name)
        barber_id = add_barber_db(shop_id, shop_name)
        
        if admin_id:
            assign_barber_telegram_id(barber_id, admin_id)
            
        bot_username = (await message_or_call_msg.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=shop_{shop_id}"
        
        msg = (
            f"✅ <b>Yangi Do'kon Yaratildi!</b>\n\n"
            f"🆔 Shop ID: <code>{shop_id}</code>\n"
            f"📛 Nom: {shop_name}\n"
            f"👤 Default Usta ID: {barber_id}\n"
        )
        
        if admin_id:
            msg += f"🔑 Admin: <code>{admin_id}</code> (Ulangan)\n"
        else:
            msg += f"⚠️ Admin: <b>Biriktirilmagan</b>\n"
            
        msg += f"\n🔗 <b>Havola:</b>\n{link}"
        
        await message_or_call_msg.answer(msg, parse_mode="HTML", reply_markup=boss_main_keyboard())
    except Exception as e:
        await message_or_call_msg.answer(f"❌ Xatolik yuz berdi: {e}", reply_markup=boss_main_keyboard())
        
    await state.clear()

@router.message(Command("my_id"))
async def cmd_my_id(message: types.Message):
    await message.answer(f"Sizning ID: <code>{message.from_user.id}</code>\nBuni /boss ga berishingiz mumkin.", parse_mode="HTML")
