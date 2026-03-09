import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.bot.handlers_owner import cb_block_lunch

async def test():
    call = MagicMock()
    call.from_user.id = 1292975621
    call.message = AsyncMock()
    
    try:
        await cb_block_lunch(call)
        print("Success!")
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
