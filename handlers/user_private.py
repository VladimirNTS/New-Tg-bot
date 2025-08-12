import uuid
from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import Command
import time
import os
from urllib.parse import quote

import qrcode
from filters.users_filter import BlockedUsersFilter

from kbds.inline import get_callback_btns, get_inlineMix_btns, get_url_btns
from database.queries import (
    orm_change_user_status,
    orm_get_tariffs,
    orm_get_faq,
    orm_get_user,
    orm_add_user,
)

user_private_router = Router()
user_private_router.message.filter(BlockedUsersFilter())

@user_private_router.message(Command("start"))
async def start(message: types.Message, session):
    await orm_add_user(session=session, user_id=message.from_user.id, name=message.from_user.full_name+str(uuid.uuid4()).split('-')[0])
    await message.answer_photo(
        photo=types.FSInputFile("img/banner.png"),
        caption="<b>SkynetVPN это безопасный доступ в один клик</b>\nС нами Вы под надёжной защитой\nНикто не должен следить за тем, что вы смотрите", 
        reply_markup=get_inlineMix_btns(
            btns={"📄 Оформить подписку": "choosesubscribe", "🔍 Проверить подписку": "check_subscription", "🤝 реферальная програма": "referral_program", "❓ FAQ": "faq", "☎ Поддержка": "https://t.me/skynetaivpn_support"}, 
            sizes=(1,1,1,2)
        )
    )
    

@user_private_router.callback_query(F.data=='back_menu')
async def start(callback: types.CallbackQuery):
    photo = types.InputMediaPhoto(
			media=types.FSInputFile("img/banner.png"),  # или BufferedInputFile для файла в памяти
			caption=f"<b>SkynetVPN это безопасный доступ в один клик.</b>\nС нами Вы под надёжной защитой.\nНикто не должен следить за тем, что вы смотрите."
		)
	
    await callback.message.edit_media(
        media=photo,
        reply_markup=get_inlineMix_btns(
            btns={"📄 Оформить подписку": "choosesubscribe", "🔍 Проверить подписку": "check_subscription", "🤝 реферальная програма": "referral_program", "❓ FAQ": "faq", "☎ Поддержка": "https://t.me/skynetaivpn_support"}, 
            sizes=(1,1,1,2)
        )
    )


@user_private_router.callback_query(F.data == 'choosesubscribe')
async def choose_subscribe(callback: types.CallbackQuery, session):
    user = await orm_get_user(session, callback.from_user.id)
    tariffs = await orm_get_tariffs(session)
    btns = {"⬅ Назад": "back_menu"}

    for i in tariffs:
        if i.sub_time == 1:
            btns[f'{i.sub_time} месяцев, {i.price} ₽ {'(Подписка)' if i.recuring == True else '(Единоразовая покупка)'}'] = f'{os.getenv("PAY_PAGE_URL")}/new_subscribe?user_id={user.id}&sub_id={i.id}'
        elif i.sub_time < 5:
            btns[f'{i.sub_time} месяца, {i.price} ₽ {'(Подписка)' if i.recuring == True else '(Единоразовая покупка)'}'] = f'{os.getenv("PAY_PAGE_URL")}/new_subscribe?user_id={user.id}&sub_id={i.id}'
        else:
            btns[f'{i.sub_time} месяц, {i.price} ₽ {'(Подписка)' if i.recuring == True else '(Единоразовая покупка)'}'] = f'{os.getenv("PAY_PAGE_URL")}/new_subscribe?user_id={user.id}&sub_id={i.id}'
    
    await callback.message.edit_caption(caption='<b>Выберите тариф</b>\n\n<b>Единоразовая покупка</b> - вы платите 1 раз, подписка не продлевается автоматически\n<b>Подписка</b> - деньги списываются автоматически по указаному сроку, вам лишь нужно будет подтверждать оплату 1 по кнопке в боте.', reply_markup=get_inlineMix_btns(btns=btns, sizes=(1,)))


@user_private_router.callback_query(F.data == 'referral_program')
async def referral_program_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_username = (await callback.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"

    text = callback.message.text
    
    # Генерируем уникальное имя файла
    timestamp = int(time.time())
    qr_filename = f"qr_{user_id}_{timestamp}.png"
    
    # Создаем QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    
    # Сохраняем QR-код в файл
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_filename)
    
    try:
        # Отправляем файл пользователю
        photo = types.InputMediaPhoto(
			media=types.FSInputFile(qr_filename),  # или BufferedInputFile для файла в памяти
			caption=f"Приводи друзей и бесплатно продлевай свою подписку за их покупки:\nЗа 1 мес - 15 дней \nЗа 6 мес - 30 дней \nЗа 12 мес - 45 дней\n\nВаша реферальная ссылка:\n<a src='{referral_link}'>{referral_link}</a>"
		)
        await callback.message.edit_media(media=photo, reply_markup=get_callback_btns(btns={ "⬅ Назад": "back_menu"}))
        await callback.answer()
    finally:
        # Удаляем файл после отправки (если он существует)
        if os.path.exists(qr_filename):
            os.remove(qr_filename)

    
# FAQ
@user_private_router.callback_query(F.data == "faq")
async def orders_list(callback: types.CallbackQuery, session):
    await callback.answer()
    message_text = "<b>Часто задаваемые вопросы</b>\n\n"
    orders = await orm_get_faq(session)
    number = 1
    for order in orders:
        message_text += f"{number}. {order.ask} \n{order.answer}\n\n"
        number += 1
    await callback.message.edit_caption(
            caption=message_text,
            reply_markup=get_callback_btns(btns={ "⬅ Назад": "back_menu"})
        )


# Check subscription
@user_private_router.callback_query(F.data.startswith('check_subscription'))
async def check_subscription(callback: types.CallbackQuery, session):
    user_id = callback.from_user.id
    user = await orm_get_user(session, user_id)

    url = f'v2raytun://{user.sub_id}@super.skynetvpn.ru:443?type=tcp&security=tls&fp=chrome&alpn=h3%2Ch2%2Chttp%2F1.1&flow=xtls-rprx-vision#SkynetVPN-{quote(user.name)}'
    
    if user.status > 0:
        await callback.message.edit_caption(caption=f"Текущий тариф: f'{i.sub_time} месяцев, {i.price} ₽ {'(Подписка)' if i.recuring == True else '(Единоразовая покупка)'}'\nВаша подписка действует до {user.sub_end}. \nВаша ссылка для подключения <code>{url}</code>", reply_markup=get_callback_btns(btns={ "⬅ Назад": "back_menu"}))
    else:
        await callback.answer("У вас нет активной подписки")


# Создание подписки для пользователя после оплаты
async def create_subscription(sub_data: dict, session, user_id, tariff, bot):
    date = sub_data['expire_time'] / 1000 
    date = datetime.fromtimestamp(date)

    await orm_change_user_status(session, user_id=user_id, new_status=tariff.id, tun_id=str(sub_data['id']), sub_end=date)
    url = f'v2raytun://{sub_data['id']}@super.skynetvpn.ru:443?type=tcp&security=tls&fp=chrome&alpn=h3%2Ch2%2Chttp%2F1.1&flow=xtls-rprx-vision#SkynetVPN-{quote(sub_data["email"])}'
    await bot.send_message(user_id, f"<b>Оплата прошла успешно!</b>\nВаша подписка на активна до {date}\n\nВаша ссылка для подключения <code>{url}</code>\n\nСпасибо за покупку! \n\nЕсли у вас есть вопросы, не стесняйтесь задавать.", reply_markup=get_callback_btns(btns={ "⬅ Назад": "back_menu"}))



