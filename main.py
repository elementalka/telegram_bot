from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import arrests
import asyncio
import logging
from handlers import start, mfo
from checkers.arrest_queue import start_arrest_checker_worker
import sys
from aiogram.client.default import DefaultBotProperties
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
TOKEN = "7513492647:AAGPORdiqas5FZtPT7ICM7eHEyUO3ptAUPw"

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(arrests.router)
    dp.include_router(mfo.router)  
    await start_arrest_checker_worker()
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
