from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from kbds.inline import get_callback_btns
from filters.users_filter import OwnerFilter
from database.queries import (
    orm_get_users,
    orm_get_subscribers,
    orm_block_user,
    orm_get_tariffs,
    orm_add_tariff,
    orm_delete_tariff,
    orm_edit_tariff,
    orm_get_products,
    orm_add_products,
    orm_delete_products,
    orm_edit_products,
    orm_add_faq,
    orm_get_faq,
    orm_delete_faq,
    orm_edit_faq
)

admin_private_router = Router()
admin_private_router.message.filter(OwnerFilter())


@admin_private_router.message(Command("admin"))
async def start(message: types.Message):
	await message.answer("Здраствуйте, чем займемся сегодня?", reply_markup=get_callback_btns(btns={
        '📃 Упарвление тарифами': 'tariffs_list',
        '📃 Список заказов': 'orders_list',
        '📫 Рассылка': 'send',
        '⚙ Редактировать FAQ': 'edit_faq',
    }, sizes=(2,2,1)))
	

# Получить список тарифов
@admin_private_router.callback_query(F.data == 'tariffs_list')
async def choose_category(callback_query: types.CallbackQuery, session):
    await callback_query.answer()
    product_list = await orm_get_products(session)

    for product in product_list:
        await callback_query.message.answer(
            text=f"<b>Имя:</b> {product.name}\n<b>Срок:</b> {product.sub_time} дней\n<b>Цена:</b> {product.price}\n<b>ID для оплаты:</b> {product.pay_id}\n<b>Тип: единоразовый платеж</b>", 
            reply_markup=get_callback_btns(btns={'Изменить': f'editonepay_{product.id}', 'Удалить': f'deleteonepay_{product.id}'})
        )

    tariff_list = await orm_get_tariffs(session)

    for tariff in tariff_list:
        await callback_query.message.answer(
            text=f"<b>Имя:</b> {tariff.name}\n<b>Срок:</b> {tariff.sub_time} месяцев\n<b>Цена:</b> {tariff.price}\n<b>ID для оплаты:</b> {tariff.pay_id}\n<b>Тип: повторяющийся платеж</b>", 
            reply_markup=get_callback_btns(btns={'Изменить': f'edittariff_{tariff.id}', 'Удалить': f'deletetariff_{tariff.id}'})
        )
    
    if tariff_list:
        await callback_query.message.answer(
                text="Вот список тарифов ⬆", 
                reply_markup=get_callback_btns(btns={'Добавить новый тариф': f'addtariff', 'Добавить единоразовый платеж': f'addonepay'})
            )
    else:
        await callback_query.message.answer(
                text="Тарифов пока нет", 
                reply_markup=get_callback_btns(btns={'Добавить новый тариф': f'addtariff'})
            )


# FSM для добавления тарифов
class FSMAddTariff(StatesGroup):
    name = State()
    sub_time = State()
    price = State()
    pay_id = State()

# Undo text for add tariff FSM
FSMAddTariff_undo_text = {
    'FSMAddTariff:name': 'Введите название тарифа заново',
    'FSMAddTariff:sub_time': 'Введите время подписки (в днях) заново',
    'FSMAddTariff:price': 'Введите цену подписки заново',
    'FSMAddTariff:pay_id': 'Введите ссылку для оплаты заново',
}

# Cancel handler for FSMAddTariff
@admin_private_router.message(StateFilter("*"), F.text.in_({'/отмена', 'отмена'}))
async def cancel_fsm_add_tariff(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer('❌ Добавление тарифа отменено')

# Back handler for FSMAddTariff
@admin_private_router.message(StateFilter('FSMAddTariff'), F.text.in_({'/назад', 'назад'}))
async def back_step_add_tariff(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == FSMAddTariff.name.state:
        await message.answer('Предыдущего шага нет, введите название тарифа или напишите "отмена"')
        return
    previous = None
    for step in FSMAddTariff.all_states:
        if step.state == current_state:
            if previous is not None:
                await state.set_state(previous.state)
                await message.answer(f"Ок, вы вернулись к прошлому шагу. {FSMAddTariff_undo_text[previous.state]}")
            return
        previous = step


@admin_private_router.callback_query(StateFilter(None), F.data == "addtariff")
async def add_product(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите название тарифа(необязательно, введите . чтобы пропустить):')
    await state.set_state(FSMAddTariff.name)


@admin_private_router.message(FSMAddTariff.name)
async def add_product_description(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(name='')
    else:
        await state.update_data(name=message.text)
    
    await message.answer('Введите время подписки (в месяцах):')
    await state.set_state(FSMAddTariff.sub_time)


@admin_private_router.message(FSMAddTariff.sub_time)
async def add_product_description(message: types.Message, state: FSMContext):
    try:
        await state.update_data(sub_time=int(message.text))
        await message.answer('Введите цену подписки:')
        await state.set_state(FSMAddTariff.price)
    except:
         await message.answer('Неверный формат. Введите время подписки (в месяцах) еще раз:')


@admin_private_router.message(FSMAddTariff.price)
async def add_product_description(message: types.Message, state: FSMContext):
    try:
        await state.update_data(price=int(message.text))
        await message.answer('Введите ссылку для оплаты:')
        await state.set_state(FSMAddTariff.pay_id)
    except:
         await message.answer('Неверный формат. Введите цену еще раз:')


@admin_private_router.message(FSMAddTariff.pay_id)
async def add_product(message: types.Message, state: FSMContext, session):
    await state.update_data(pay_id=message.text.split('=')[-1])
    await message.answer('✅ Тариф добавлен')
    data = await state.get_data()
    await orm_add_tariff(session=session, data=data)
    await state.clear()


# Удаление тарифа
@admin_private_router.callback_query(F.data.startswith('deletetariff_'))
async def delete_product(callback_query: types.CallbackQuery, session):
    await callback_query.answer()
    await orm_delete_tariff(session, callback_query.data.split('_')[-1])
    await callback_query.message.answer("✅ Тариф удален")
    await callback_query.message.delete()


# Редактирование единоразового платежа
class FSMEditTariff(StatesGroup):
    name = State()
    sub_time = State()
    price = State()
    pay_id = State()


@admin_private_router.callback_query(StateFilter(None), F.data.startswith("edittariff"))
async def add_product(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(tariff_id=callback.data.split('_')[-1])
    await callback.answer()
    await callback.message.answer('Вы создаете новый тариф. Для отмены напишите /отмена или /назад')
    await callback.message.answer('Введите новое название тарифа(необязательно, введите . чтобы пропустить):')
    await state.set_state(FSMEditTariff.name)


@admin_private_router.message(FSMEditTariff.name)
async def edit_tariff_name(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(name=None)
    else:
        await state.update_data(name=message.text)
    await message.answer('Введите новое время подписки (в месяцах) (или . чтобы пропустить):')
    await state.set_state(FSMEditTariff.sub_time)

@admin_private_router.message(FSMEditTariff.sub_time)
async def edit_tariff_sub_time(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(sub_time=None)
        await message.answer('Введите новую цену подписки (или . чтобы пропустить):')
        await state.set_state(FSMEditTariff.price)
        return
    try:
        await state.update_data(sub_time=int(message.text))
        await message.answer('Введите новую цену подписки (или . чтобы пропустить):')
        await state.set_state(FSMEditTariff.price)
    except:
        await message.answer('Неверный формат. Введите время подписки (в месяцах) еще раз:')

@admin_private_router.message(FSMEditTariff.price)
async def edit_tariff_price(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(price=None)
        await message.answer('Введите новую ссылку для оплаты (или . чтобы пропустить):')
        await state.set_state(FSMEditTariff.pay_id)
        return
    try:
        await state.update_data(price=int(message.text))
        await message.answer('Введите новую ссылку для оплаты (или . чтобы пропустить):')
        await state.set_state(FSMEditTariff.pay_id)
    except:
        await message.answer('Неверный формат. Введите цену еще раз:')

@admin_private_router.message(FSMEditTariff.pay_id)
async def edit_tariff_pay_id(message: types.Message, state: FSMContext, session):
    if message.text == '.':
        await state.update_data(pay_id=None)
    else:
        await state.update_data(pay_id=message.text.split('=')[-1])
    data = await state.get_data()
    # Оставляем только те поля, которые не None
    update_fields = {k: v for k, v in data.items() if v is not None}
    del update_fields['tariff_id']
    await message.answer('✅ Тариф изменен')
    await orm_edit_tariff(session=session, tariff_id=data['tariff_id'], fields=update_fields)
    await state.clear()


# FSM для добавления единоразового платежа
class FSMAddOnePay(StatesGroup):
    name = State()
    sub_time = State()
    price = State()
    pay_id = State()

# Undo text for add tariff FSM
FSMAddOnePay_undo_text = {
    'FSMAddTariff:name': 'Введите название платежа заново',
    'FSMAddTariff:sub_time': 'Введите время платежа (в днях) заново',
    'FSMAddTariff:price': 'Введите цену платежа заново',
    'FSMAddTariff:pay_id': 'Введите ссылку для оплаты заново',
}

# Cancel handler for FSMAddTariff
@admin_private_router.message(StateFilter("*"), F.text.in_({'/отмена', 'отмена'}))
async def cancel_fsm_add_tariff(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer('❌ Добавление платежа отменено')

# Back handler for FSMAddTariff
@admin_private_router.message(StateFilter('FSMAddOnePay'), F.text.in_({'/назад', 'назад'}))
async def back_step_add_tariff(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == FSMAddOnePay.name.state:
        await message.answer('Предыдущего шага нет, введите название платежа или напишите "отмена"')
        return
    previous = None
    for step in FSMAddOnePay.all_states:
        if step.state == current_state:
            if previous is not None:
                await state.set_state(previous.state)
                await message.answer(f"Ок, вы вернулись к прошлому шагу. {FSMAddOnePay_undo_text[previous.state]}")
            return
        previous = step


@admin_private_router.callback_query(StateFilter(None), F.data == "addonepay")
async def add_product(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите название платежа(необязательно, введите . чтобы пропустить):')
    await state.set_state(FSMAddOnePay.name)


@admin_private_router.message(FSMAddOnePay.name)
async def add_product_description(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(name='')
    else:
        await state.update_data(name=message.text)
    
    await message.answer('Введите время подписки (в днях):')
    await state.set_state(FSMAddOnePay.sub_time)


@admin_private_router.message(FSMAddOnePay.sub_time)
async def add_product_description(message: types.Message, state: FSMContext):
    try:
        await state.update_data(sub_time=int(message.text))
        await message.answer('Введите цену платежа:')
        await state.set_state(FSMAddOnePay.price)
    except:
         await message.answer('Неверный формат. Введите время подписки (в днях) еще раз:')


@admin_private_router.message(FSMAddOnePay.price)
async def add_product_description(message: types.Message, state: FSMContext):
    try:
        await state.update_data(price=int(message.text))
        await message.answer('Введите ссылку для оплаты:')
        await state.set_state(FSMAddOnePay.pay_id)
    except:
         await message.answer('Неверный формат. Введите цену еще раз:')


@admin_private_router.message(FSMAddOnePay.pay_id)
async def add_product(message: types.Message, state: FSMContext, session):
    await state.update_data(pay_id=message.text.split('=')[-1])
    await message.answer('✅ Тариф добавлен')
    data = await state.get_data()
    await orm_add_products(session=session, data=data)
    await state.clear()


# Удаление единоразового платежа
@admin_private_router.callback_query(F.data.startswith('deleteonepay_'))
async def delete_product(callback_query: types.CallbackQuery, session):
    await callback_query.answer()
    await orm_delete_products(session, callback_query.data.split('_')[-1])
    await callback_query.message.answer("✅ Платежа удален")
    await callback_query.message.delete()


# Редактирование единоразового платежа
class FSMEditOnePay(StatesGroup):
    name = State()
    sub_time = State()
    price = State()
    pay_id = State()


@admin_private_router.callback_query(StateFilter(None), F.data.startswith("editonepay"))
async def add_product(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(tariff_id=callback.data.split('_')[-1])
    await callback.answer()
    await callback.message.answer('Введите новое название платежа(необязательно, введите . чтобы пропустить):')
    await state.set_state(FSMEditOnePay.name)


@admin_private_router.message(FSMEditOnePay.name)
async def edit_tariff_name(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(name=None)
    else:
        await state.update_data(name=message.text)
    await message.answer('Введите новое время подписки (в днях) (или . чтобы пропустить):')
    await state.set_state(FSMEditOnePay.sub_time)

@admin_private_router.message(FSMEditOnePay.sub_time)
async def edit_tariff_sub_time(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(sub_time=None)
        await message.answer('Введите новую цену подписки (или . чтобы пропустить):')
        await state.set_state(FSMEditOnePay.price)
        return
    try:
        await state.update_data(sub_time=int(message.text))
        await message.answer('Введите новую цену подписки (или . чтобы пропустить):')
        await state.set_state(FSMEditOnePay.price)
    except:
        await message.answer('Неверный формат. Введите время подписки (в днях) еще раз:')

@admin_private_router.message(FSMEditOnePay.price)
async def edit_tariff_price(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(price=None)
        await message.answer('Введите новую ссылку для оплаты (или . чтобы пропустить):')
        await state.set_state(FSMEditOnePay.pay_id)
        return
    try:
        await state.update_data(price=int(message.text))
        await message.answer('Введите новую ссылку для оплаты (или . чтобы пропустить):')
        await state.set_state(FSMEditOnePay.pay_id)
    except:
        await message.answer('Неверный формат. Введите цену еще раз:')

@admin_private_router.message(FSMEditOnePay.pay_id)
async def edit_tariff_pay_id(message: types.Message, state: FSMContext, session):
    if message.text == '.':
        await state.update_data(pay_id=None)
    else:
        await state.update_data(pay_id=message.text.split('=')[-1])
    data = await state.get_data()
    # Оставляем только те поля, которые не None
    update_fields = {k: v for k, v in data.items() if v is not None}
    del update_fields['tariff_id']
    await message.answer('✅ Тариф изменен')
    await orm_edit_products(session=session, tariff_id=data['tariff_id'], fields=update_fields)
    await state.clear()


# FAQ
@admin_private_router.callback_query(F.data == 'edit_faq')
async def edit_faq(callback: types.CallbackQuery, state: FSMContext, session):
    
    await callback.answer()
    faq_list = await orm_get_faq(session)
    for faq in faq_list:
        await callback.message.answer(
            text=f"<b>Вопрос:</b> {faq.ask}\n<b>Ответ:</b> {faq.answer}",
            reply_markup=get_callback_btns(btns={'Изменить': f'editfaq_{faq.id}', 'Удалить': f'deletefaq_{faq.id}'})
        )
    if faq_list:
        await callback.message.answer(
                text="Вот список вопросов ⬆",
                reply_markup=get_callback_btns(btns={'Добавить новый вопрос': f'addfaq'})
            )
    else:
        await callback.message.answer(
                text="Вопросов пока нет",
                reply_markup=get_callback_btns(btns={'Добавить новый вопрос': f'addfaq'})
            )


# FSM для добавления вопросов
class FSMAddFAQ(StatesGroup):
    ask = State()
    answer = State()


@admin_private_router.callback_query(StateFilter(None), F.data == "addfaq")
async def add_faq(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите вопрос:')
    await state.set_state(FSMAddFAQ.ask)


@admin_private_router.message(FSMAddFAQ.ask)
async def add_faq_description(message: types.Message, state: FSMContext):
    await state.update_data(ask=message.text)
    await message.answer('Введите ответ:')
    await state.set_state(FSMAddFAQ.answer)


@admin_private_router.message(FSMAddFAQ.answer)
async def add_faq_description(message: types.Message, state: FSMContext, session):
    await state.update_data(answer=message.text)
    await message.answer('✅ Вопрос добавлен')
    data = await state.get_data()
    await orm_add_faq(session=session, data=data)
    await state.clear()


# FSM изменения вопросов
class FSMEditFAQ(StatesGroup):
    id = State()
    ask = State()
    answer = State()


@admin_private_router.callback_query(StateFilter(None), F.data.startswith("editfaq"))
async def edit_faq(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(faq_id=callback.data.split('_')[-1])
    await callback.answer()
    await callback.message.answer('Вы редактируете вопрос. Для отмены напишите /отмена или /назад')
    await callback.message.answer('Введите новый вопрос, для пропуска напишите ".":')
    await state.set_state(FSMEditFAQ.ask)


@admin_private_router.message(FSMEditFAQ.ask)
async def edit_faq_name(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(ask=None)
    else:
        await state.update_data(ask=message.text)
    await message.answer('Введите новый ответ, для пропуска напишите ".":')
    await state.set_state(FSMEditFAQ.answer)


@admin_private_router.message(FSMEditFAQ.answer)
async def edit_faq_description(message: types.Message, state: FSMContext, session):
    if message.text == '.':
        await state.update_data(answer=None)
    else:
        await state.update_data(answer=message.text)
    data = await state.get_data()
    # Оставляем только те поля, которые не None
    update_fields = {k: v for k, v in data.items() if v is not None}
    del update_fields['faq_id']
    await message.answer('✅ Вопрос изменен')
    await orm_edit_faq(session=session, id=data['faq_id'], fields=update_fields)
    await state.clear()


# Удаление вопроса
@admin_private_router.callback_query(F.data.startswith('deletefaq_'))
async def delete_faq(callback_query: types.CallbackQuery, session):
    await callback_query.answer()
    await orm_delete_faq(session, callback_query.data.split('_')[-1])
    await callback_query.message.answer("✅ Вопрос удален")
    await callback_query.message.delete()


class FSMSendMessages(StatesGroup):
    message = State()
    picture = State()
    recipients = State()


@admin_private_router.callback_query(StateFilter(None), F.data == "send")
async def send_messages(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите сообщение для отправки:')
    await state.set_state(FSMSendMessages.message)


@admin_private_router.message(FSMSendMessages.message)
async def send_messages_description(message: types.Message, state: FSMContext):
    await state.update_data(message=message.text)
    await message.answer('Отправте картинку если нужна. Если не нужна то отправте ".":')
    await state.set_state(FSMSendMessages.picture)


@admin_private_router.message(FSMSendMessages.picture, or_f(F.photo, F.text))
async def send_messages_picture(message: types.Message, state: FSMContext):
    if message.text == '.':
        await message.answer('Выберите кому отправить сообщение: активные подписчики или все (включая гостей).', reply_markup=get_callback_btns(btns={'Активные подписчики': 'active_subscribers', 'Все': 'all'}))
        await state.set_state(FSMSendMessages.recipients)
    else:
        await state.update_data(picture=message.photo[0].file_id)
        await message.answer('Выберите кому отправить сообщение: активные подписчики или все (включая гостей).', reply_markup=get_callback_btns(btns={'Активные подписчики': 'active_subscribers', 'Все': 'all'}))
        await state.set_state(FSMSendMessages.recipients)


@admin_private_router.callback_query(FSMSendMessages.recipients, F.data == "active_subscribers")
async def send_messages_active_subscribers(callback: types.CallbackQuery, state: FSMContext, session, bot):
    await callback.answer()
    users = await orm_get_subscribers(session)
    for user in users:
        data = await state.get_data()

        if data.get('picture'):
            await bot.send_photo(chat_id=user.user_id, photo=data['picture'], caption=data['message'])
        else:
            await bot.send_message(chat_id=user.user_id, text=data['message'])
        
    
    await callback.message.answer(f"Сообщение отправленно {len(users)} пользователям")
    await state.clear()


@admin_private_router.callback_query(FSMSendMessages.recipients, F.data == "all")
async def send_messages_active_subscribers(callback: types.CallbackQuery, state: FSMContext, session, bot):
    await callback.answer()
    users = await orm_get_users(session)
    for user in users:
        data = await state.get_data()
        if data.get('picture'):
            await bot.send_photo(chat_id=user.user_id, photo=data['picture'], caption=data['message'])
        else:
            await bot.send_message(chat_id=user.user_id, text=data['message'])
    
    await callback.message.answer(f"Сообщение отправленно {len(users)} пользователям")
    await state.clear()


# Заказы 
@admin_private_router.callback_query(StateFilter(None), F.data == "orders_list")
async def orders_list(callback: types.CallbackQuery, session):
    await callback.answer()
    message_text = ""
    orders = await orm_get_users(session)
    for order in orders:
        if order.status > 0:
            message_text = f"<b>ID:</b> {order.user_id}\n<b>Имя:</b> {order.name}\n<b>Статус:</b> {order.status}\n"
    

    if message_text:
        await callback.message.answer(
            text=message_text,
            reply_markup=get_callback_btns(btns={'Заблокировать пользователя': f'blockuser_{order.user_id}'})
        )
        await callback.message.answer(
                text="Вот список заказов ⬆",
            )
    else:
        await callback.message.answer(
                text="Заказов пока нет",
            )
