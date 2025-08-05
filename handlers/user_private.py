from aiogram import Router, types, F
from aiogram.filters import Command

from filters.users_filter import BlockedUsersFilter

from kbds.inline import get_callback_btns
from database.queries import (
    orm_get_tariffs
)

user_private_router = Router()
user_private_router.message.filter(BlockedUsersFilter())

@user_private_router.message(Command("start"))
async def start(message: types.Message):
	await message.answer("hello", reply_markup=get_callback_btns(btns={"📄 Оформить подписку": "choosesubscribe", "🔍 Проверить подписку": "check_subscription", "🤝 реферальная програма": "referral_program", "❓ FAQ": "faq", "☎ Поддержка": "support"}, sizes=(1,1,1,2)))


@user_private_router.callback_query(F.data == 'choosesubscribe')
async def choose_subscribe(callback, session):
    tariffs = await orm_get_tariffs(session)
    btns = {}
    for i in tariffs:
        if i.sub_time > 1:
            btns[f'{i.sub_time} месяцев, {i.price} ₽'] = str(i.id)
        else:
            btns[f'{i.sub_time} месяц, {i.price} ₽'] = 'buy_' + str(i.id)
    
    await callback.message.answer('Выберите тариф', reply_markup=get_callback_btns(btns=btns, sizes=(1,)))







