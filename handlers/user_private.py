from aiogram import Router, types
from aiogram.filters import Command

from filters.users_filter import BlockedUsersFilter

from kbds.inline import get_callback_btns

user_private_router = Router()
user_private_router.message.filter(BlockedUsersFilter())

@user_private_router.message(Command("start"))
async def start(message: types.Message):
	await message.answer("hello", reply_markup=get_callback_btns(btns={"📄 Оформить подписку": "subscribe", "🔍 Проверить подписку": "check_subscription", "🤝 реферальная програма": "referral_program", "❓ FAQ": "faq", "☎ Поддержка": "support"}, sizes=(1,1,1,2)))

