from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from kbds.inline import get_callback_btns
from filters.users_filter import OwnerFilter
from database.queries import (
    orm_get_users,
    orm_get_tariffs,
    orm_add_tariff,
    orm_delete_tariff,
    orm_edit_tariff
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
    tariff_list = await orm_get_tariffs(session)

    for tariff in tariff_list:
        await callback_query.message.answer(
            text=f"<b>Имя:</b> {tariff.name}\n<b>Срок:</b> {tariff.sub_time} дней\n<b>Цена:</b> {tariff.price}\n<b>ID для оплаты:</b> {tariff.pay_id}", 
            reply_markup=get_callback_btns(btns={'Изменить': f'edittariff_{tariff.id}', 'Удалить': f'deletetariff_{tariff.id}'})
        )
    
    if tariff_list:
        await callback_query.message.answer(
                text="Вот список тарифов ⬆", 
                reply_markup=get_callback_btns(btns={'Добавить новый тариф': f'addtariff'})
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
    
    await message.answer('Введите время подписки (в днях):')
    await state.set_state(FSMAddTariff.sub_time)


@admin_private_router.message(FSMAddTariff.sub_time)
async def add_product_description(message: types.Message, state: FSMContext):
    try:
        await state.update_data(sub_time=int(message.text))
        await message.answer('Введите цену подписки:')
        await state.set_state(FSMAddTariff.price)
    except:
         await message.answer('Неверный формат. Введите время подписки (в днях) еще раз:')


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


# Редактирование тарифа
class FSMEditCategory(StatesGroup):
    name = State()
    sub_time = State()
    price = State()
    pay_id = State()


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
    
    await message.answer('Введите время подписки (в днях):')
    await state.set_state(FSMAddTariff.sub_time)


@admin_private_router.message(FSMAddTariff.sub_time)
async def add_product_description(message: types.Message, state: FSMContext):
    try:
        await state.update_data(sub_time=int(message.text))
        await message.answer('Введите цену подписки:')
        await state.set_state(FSMAddTariff.price)
    except:
         await message.answer('Неверный формат. Введите время подписки (в днях) еще раз:')


@admin_private_router.message(FSMAddTariff.price)
async def add_product_description(message: types.Message, state: FSMContext):
    try:
        await state.update_data(price=int(message.text))
        await message.answer('Введите ссылку для оплаты:')
        await state.set_state(FSMAddTariff.pay_id)
    except:
         await message.answer('Неверный формат. Введите цену еще раз:')


@admin_private_router.message(FSMEditCategory.name, F.text)
async def edit_category(message: types.Message, state: FSMContext, session):
    category_id = await state.get_data()
    await message.answer(f"✅ Название категории измененно на {message.text}")
    await orm_edit_tariff(session=session, category_id=category_id['category_id'], name=message.text)

    await state.clear()


# # Получить список товара
# @admin_private_router.callback_query(F.data == 'products_list')
# async def choose_category(callback_query: types.CallbackQuery, session):
#     await callback_query.answer()
#     category_list = await orm_get_categories(session)

#     await callback_query.message.answer(
#         text='Выберите категорию:', 
#         reply_markup=get_callback_btns(btns={str(i.name): 'category_'+str(i.id) for i in category_list})
#     )


# @admin_private_router.callback_query(F.data.startswith('category_'))
# async def send_products_list(callback_query: types.CallbackQuery, session):
#     await callback_query.answer()
#     products_list = await orm_get_products(session, callback_query.data.split('_')[-1])

#     for product in products_list:
#         await callback_query.message.answer_photo(
#             photo=product.image, 
#             caption=f"<b>Имя:</b> {product.name}\n<b>Описание:</b> {product.description}\n\n<b>Цена:</b> {product.price}",
#             reply_markup=get_callback_btns(btns={'Изменить': f'editproduct_{product.id}', 'Удалить': f'deleteproduct_{product.id}'})
#             )

#     await callback_query.message.answer("✅ Вот список товаров ⬆️")


# # Удаление товара
# @admin_private_router.callback_query(StateFilter('*'), F.data.startswith('deleteproduct_'))
# async def delete_product(callback_query: types.CallbackQuery, session):
#     await callback_query.answer()
#     await orm_delete_product(session, callback_query.data.split('_')[-1])
#     await callback_query.message.answer("✅ Товар удален")
#     await callback_query.message.delete()


# # Хендлер для отлова отмены FSM
# @admin_private_router.message(StateFilter('*'), Command('отмена'))
# async def CanselFSM(message: types.Message, state: FSMContext):
#     currant_state = state.get_state()
#     if currant_state == None:
#         return
    
#     await state.clear()
#     await message.answer('❌ Действия отменены')






# # FSM для добавления товара
# class FSMAddProduct(StatesGroup):
#     name = State()
#     description = State()
#     price = State()
#     image = State()
#     category_id = State()

#     undo_text = {
# 		'FSMAddProduct:name': 'Введите название заного',
#         'FSMAddProduct:description': 'Введите описание заного',
# 		'FSMAddProduct:price': 'Введите цену заного',
#         'FSMAddProduct:image': 'Пришлите изображение заного',
#         'FSMAddProduct:category_id': 'Выберите категорию заного',
#     }


# @admin_private_router.message(StateFilter('FSMAddProduct'), Command("назад"))
# async def back_step_handler(message: types.Message, state: FSMContext) -> None:
#     '''Шаг назад'''

#     current_state = await state.get_state()

#     if current_state == FSMAddProduct.name:
#         await message.answer('Предидущего шага нет, или введите название товара или напишите "отмена"')
#         return

#     previous = None
#     for step in FSMAddProduct.all_states:
#         if step.state == current_state:
#             await state.set_state(previous)
#             await message.answer(f"Ок, вы вернулись к прошлому шагу \n {FSMAddProduct.undo_text[previous.state]}")
#             return
#         previous = step


# @admin_private_router.callback_query(StateFilter(None), F.data == "add_product")
# async def add_product(callback: types.CallbackQuery, state: FSMContext):
#     await callback.answer()
#     await callback.message.answer('<b>Добавление товара</b>\nДля отмены пишите: /отмена \nЧтобы сделать шаг назад пишите: /назад \n\nВведите название товара:')
#     await state.set_state(FSMAddProduct.name)


# @admin_private_router.message(FSMAddProduct.name)
# async def add_product_name(message: types.Message, state: FSMContext):
#     await state.update_data(name=message.text)
#     await message.answer('Введите описание товара:')
#     await state.set_state(FSMAddProduct.description)


# @admin_private_router.message(FSMAddProduct.description)
# async def add_product_description(message: types.Message, state: FSMContext):
#     await state.update_data(description=message.text)
#     await message.answer('Введите цену товара:')
#     await state.set_state(FSMAddProduct.price)


# @admin_private_router.message(FSMAddProduct.price)
# async def add_product_price(message: types.Message, state: FSMContext):
#     try:
#         await state.update_data(price=float(message.text))
#         await message.answer('Пришлите изображение товара:')
#         await state.set_state(FSMAddProduct.image)
#     except:
#          await message.answer("Вы ввели не число, попробуйте ещё раз:")


# @admin_private_router.message(FSMAddProduct.image, F.photo)
# async def add_product_image(message: types.Message, state: FSMContext, session):
#     await state.update_data(image=message.photo[-1].file_id)
#     categories = await orm_get_categories(session=session)
#     await message.answer('Выберите категорию:', reply_markup=get_callback_btns(btns={str(i.name): str(i.id) for i in categories}))
#     await state.set_state(FSMAddProduct.category_id)


# @admin_private_router.callback_query(FSMAddProduct.category_id)
# async def add_product_category(callback: types.CallbackQuery, state: FSMContext, session):
#     await state.update_data(category=callback.data)
#     await callback.answer()
#     await callback.message.answer('✅ Товар создан')
#     data = await state.get_data()
#     await orm_add_product(session, data)
#     await state.clear()




