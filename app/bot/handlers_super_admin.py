from aiogram import Router, types, F
from aiogram.filters import Command
import os
from app.db.repository import create_shop_db, add_barber_db, assign_barber_telegram_id

router = Router()

def is_super_admin(user_id: int) -> bool:
    # Load from ENV directly to ensure freshness
    ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    return str(user_id) in [x.strip() for x in ids]

@router.message(Command("new_shop"))
async def cmd_new_shop(message: types.Message):
    """
    Usage: /new_shop "Shop Name" (Optional: 123456789)
    """
    if not is_super_admin(message.from_user.id):
        return # Silent ignore

    try:
        # Parse args
        # /new_shop "Name" 123456
        import shlex
        args = shlex.split(message.text)
        
        if len(args) < 2:
            await message.answer("⚠️ Ishlatish: `/new_shop \"Do'kon Nomi\" [TelegramID]`")
            return
            
        shop_name = args[1]
        owner_id = int(args[2]) if len(args) > 2 else None
        
        # 1. Create Shop
        shop_id = create_shop_db(shop_name)
        
        # 2. Auto-create "Main Barber"
        barber_id = add_barber_db(shop_id, "Bosh Usta")
        
        # 3. Assign Owner if provided
        if owner_id:
            assign_barber_telegram_id(barber_id, owner_id)
        
        bot_username = (await message.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=shop_{shop_id}"
        
        msg = (
            f"✅ <b>Yangi Do'kon Yaratildi!</b>\n\n"
            f"🆔 Shop ID: <code>{shop_id}</code>\n"
            f"📛 Nom: {shop_name}\n"
            f"👤 Default Usta ID: {barber_id}\n"
        )
        
        if owner_id:
            msg += f"🔑 Admin: <code>{owner_id}</code> (Ulangan)\n"
        else:
            msg += f"⚠️ Admin: <b>Biriktirilmagan</b>\nBuyruq: `/set_admin {barber_id} TG_ID`\n"
            
        msg += f"\n🔗 <b>Mijozlar uchun havola:</b>\n{link}"
        
        await message.answer(msg)
        
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

@router.message(Command("set_admin"))
async def cmd_set_admin(message: types.Message):
    """Usage: /set_admin <barber_id> <telegram_id>"""
    if not is_super_admin(message.from_user.id): return
    
    try:
        args = message.text.split()
        barber_id = int(args[1])
        tg_id = int(args[2])
        
        assign_barber_telegram_id(barber_id, tg_id)
        await message.answer(f"✅ Barber {barber_id} ga Telegram ID {tg_id} bog'landi.")
    except:
        await message.answer("Xato: `/set_admin BARBER_ID TG_ID`")

@router.message(Command("my_id"))
async def cmd_my_id(message: types.Message):
    await message.answer(f"Sizning ID: <code>{message.from_user.id}</code>")
