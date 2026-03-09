import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_booking.py", "r", encoding="utf-8") as f:
    code = f.read()

# @router.callback_query(F.data.startswith("time_"))
# async def check_phone_step(call: types.CallbackQuery, state: FSMContext):
#     await state.update_data(time=call.data.split("_")[1])

old_check_phone = '''@router.callback_query(F.data.startswith("time_"))
async def check_phone_step(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(time=call.data.split("_")[1])'''

new_check_phone = '''@router.callback_query(F.data.startswith("time_"))
async def check_phone_step(call: types.CallbackQuery, state: FSMContext):
    # data is like time_2026-03-09_15:30
    parts = call.data.split("_")
    
    if len(parts) == 3: # time_DATE_TIME
        date_str = parts[1]
        time_str = parts[2]
        await state.update_data(date=date_str, time=time_str)
    else:
        await state.update_data(time=parts[1])
'''

code = code.replace(old_check_phone, new_check_phone)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_booking.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated check_phone_step in handlers_booking.")
