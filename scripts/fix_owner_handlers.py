import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace "status" handler for "Bugun" text matching
code = code.replace(
    '@router.message(F.text.contains("Bugun"))\n@router.message(F.text.contains("Today"))\nasync def cmd_system_health',
    '@router.message(Command("status"))\nasync def cmd_system_health'
)

# Add handler for "Bugun"
handler_bugun = '''
@router.message(F.text.contains("Bugun") | F.text.contains("Сегодня"))
@router.message(Command("today"))
async def cmd_today(message: types.Message, state: FSMContext):
    shop_id = await get_user_shop_id(message.from_user.id, state)
    if not shop_id: return
    
    today = get_today()
    bookings = list_bookings_detailed(shop_id, today)
    
    if not bookings:
        await message.answer("📅 Bugun uchun buyurtmalar yo'q / На сегодня заказов нет.")
        return
        
    report = ["📅 <b>Bugungi buyurtmalar / Заказы на сегодня:</b>\\n"]
    for b in bookings:
        time_str = b['start_at'].strftime("%H:%M")
        phone = b.get('customer_phone') or b.get('customer_username') or "N/A"
        report.append(f"⏰ {time_str} | 💇‍♂️ {b['barber_name']} | 👤 {b['customer_name']} ({phone})")
        
    await message.answer("\\n".join(report), parse_mode="HTML")

@router.message(F.text.contains("Ertaga") | F.text.contains("Завтра"))
@router.message(Command("tomorrow"))
async def cmd_tomorrow(message: types.Message, state: FSMContext):
    shop_id = await get_user_shop_id(message.from_user.id, state)
    if not shop_id: return
    
    tomorrow = get_today() + timedelta(days=1)
    bookings = list_bookings_detailed(shop_id, tomorrow)
    
    if not bookings:
        await message.answer("🗓 Ertaga uchun buyurtmalar yo'q / На завтра заказов нет.")
        return
        
    report = ["🗓 <b>Ertangi buyurtmalar / Заказы на завтра:</b>\\n"]
    for b in bookings:
        time_str = b['start_at'].strftime("%H:%M")
        phone = b.get('customer_phone') or b.get('customer_username') or "N/A"
        report.append(f"⏰ {time_str} | 💇‍♂️ {b['barber_name']} | 👤 {b['customer_name']} ({phone})")
        
    await message.answer("\\n".join(report), parse_mode="HTML")
'''

code = code.replace('# --- ADMIN MENU HANDLERS ---', '# --- ADMIN MENU HANDLERS ---\n' + handler_bugun)

# Fix "Barcha buyurtmalar" text matching
code = re.sub(
    r'@router\.message\(F\.text == ".*Barcha buyurtmalar.*"\)',
    '@router.message(F.text.contains("Barcha buyurtmalar") | F.text.contains("Все заказы"))',
    code
)

# Fix "Mijoz rejimi" text matching
code = re.sub(
    r'@router\.message\(F\.text == ".*Mijoz rejimi.*"\)',
    '@router.message(F.text.contains("Mijoz rejimi") | F.text.contains("Режим клиента"))',
    code
)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_owner.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Fixed owner handlers.")
