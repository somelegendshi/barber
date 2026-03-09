import re

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "r", encoding="utf-8") as f:
    code = f.read()

old_logic = '''@router.callback_query(F.data.startswith("edit_day_"))
async def edit_day_start(call: types.CallbackQuery):
    data_parts = call.data.split("_")
    dow = int(data_parts[2])
    
    # Check if we are coming from a WH record or just the DOW
    # If data is edit_day_wh_ID
    wh_id = None
    if len(data_parts) > 3 and data_parts[2] == "wh":
        wh_id = int(data_parts[3])
        wh = get_work_hour_by_id(wh_id)
        dow = wh['dow']
    else:'''

new_logic = '''@router.callback_query(F.data.startswith("edit_day_"))
async def edit_day_start(call: types.CallbackQuery):
    data_parts = call.data.split("_")
    
    # Check if we are coming from a WH record or just the DOW
    # If data is edit_day_wh_ID
    wh_id = None
    if len(data_parts) > 2 and data_parts[2] == "wh":
        wh_id = int(data_parts[3])
        wh = get_work_hour_by_id(wh_id)
        dow = wh['dow']
    else:
        dow = int(data_parts[2])'''

code = code.replace(old_logic, new_logic)

with open(r"C:\Users\Legion\Documents\barber_booking_bot\app\bot\handlers_admin_settings.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Fixed edit_day_wh parsing bug.")
