from aiogram import Router, types, F
from aiogram.filters import Command
from app.db.repository import list_customer_bookings, cancel_booking_by_customer
from app.bot.keyboards import my_booking_keyboard
from aiogram.fsm.context import FSMContext
import os

router = Router()

@router.message(F.text == "📅 Mening buyurtmalarim")
@router.message(F.text == "📅 Мои записи")
@router.message(Command("my"))
async def cmd_my_bookings(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # FIXED: Check bookings for ALL shops the customer might have registered in
    bookings = list_customer_bookings(user_id, None)
    
    if not bookings:
        msg_text = "🤷‍♂️ Sizda faol buyurtmalar yo'q." if lang == "uz" else "🤷‍♂️ У вас нет активных записей."
        await message.answer(msg_text)
        return
        
    header_text = "📅 <b>Sizning faol buyurtmalaringiz:</b>" if lang == "uz" else "📅 <b>Ваши активные записи:</b>"
    await message.answer(header_text)
    
    for b in bookings:
        time_str = b['start_at'].strftime("%d.%m %H:%M")
        
        # Labels
        lbl_master = "Usta" if lang == "uz" else "Мастер"
        lbl_time = "Vaqt" if lang == "uz" else "Время"
        
        msg = (
            f"✂️ <b>{b['service_name']}</b>\n"
            f"👤 {lbl_master}: {b['barber_name']}\n"
            f"🕒 {lbl_time}: {time_str}\n"
            f"🆔 ID: <code>{b['id']}</code>"
        )
        # Attach inline keyboard for actions
        await message.answer(msg, reply_markup=my_booking_keyboard(b['id'], lang=lang))

@router.callback_query(F.data.startswith("cancel_me_"))
async def cancel_my_booking(call: types.CallbackQuery, state: FSMContext):
    booking_id = int(call.data.split("_")[2])
    
    # Get State for Shop ID logic
    data = await state.get_data()
    lang = data.get("lang", "uz")
    shop_id = data.get("active_shop_id", int(os.getenv("SHOP_ID", "1")))
    
    success = cancel_booking_by_customer(booking_id, shop_id, reason="User Cancelled")
    
    if success:
        msg_text = f"✅ Buyurtma {booking_id} bekor qilindi." if lang == "uz" else f"✅ Заказ {booking_id} отменен."
        await call.message.edit_text(msg_text)
    else:
        err_text = "Xatolik: Buyurtma topilmadi" if lang == "uz" else "Ошибка: Заказ не найден"
        await call.answer(err_text, show_alert=True)

@router.callback_query(F.data.startswith("reschedule_"))
async def reschedule_booking(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    
    # Bilingual Alert
    alert_text = (
        "Qayta band qilish uchun avval bekor qiling, keyin yangisini yarating." 
        if lang == "uz" else 
        "Чтобы перенести, сначала отмените запись, затем создайте новую."
    )
    await call.answer(alert_text, show_alert=True)
