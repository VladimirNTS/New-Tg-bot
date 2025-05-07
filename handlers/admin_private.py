from aiogram import Router, types
from aiogram.filters import Command

from kbds.inline import get_callback_btns
from filters.users_filter import OwnerFilter

admin_private_router = Router()
admin_private_router.message.filter(OwnerFilter())


@admin_private_router.message(Command("admin"))
async def start(message: types.Message):
	await message.answer("Здраствуйте, чем займемся сегодня?", reply_markup=get_callback_btns(btns={
        'Список товаров': 'products_list',
        'Добавить товар': 'add_product',
        'Добавить категорию': 'add_catigory',
        'Настройки': 'settings'
    }, sizes=(1,2,1)))
