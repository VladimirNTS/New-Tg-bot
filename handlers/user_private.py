from aiogram import Router, types
from aiogram.filters import Command

from filters.users_filter import BlockedUsersFilter


user_private_router = Router()
user_private_router.message.filter(BlockedUsersFilter())

@user_private_router.message(Command("start"))
async def start(message: types.Message):
	await message.answer("hello")

