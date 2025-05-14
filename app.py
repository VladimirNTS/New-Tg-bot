import os

import asyncio
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
load_dotenv()

from handlers.user_private import user_private_router
from handlers.admin_private import admin_private_router
from database.engine import session, create_db
from middlewares.db_session import DataBaseSession


bot = Bot(token=os.getenv('TOKEN'))

dp = Dispatcher()

dp.include_router(user_private_router)
dp.include_router(admin_private_router)


async def on_startup():
    await create_db()


async def main():
    dp.startup.register(on_startup)
    dp.update.middleware.register(DataBaseSession(session_pool=session))

    await dp.start_polling(bot)


asyncio.run(main())




