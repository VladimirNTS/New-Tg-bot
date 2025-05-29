from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from kbds.inline import get_callback_btns
from filters.users_filter import OwnerFilter
from database.queries import (
    orm_add_product, 
    orm_create_categories, 
    orm_get_categories, 
    orm_get_products,
    orm_edit_category,
    orm_delete_product
)

admin_private_router = Router()
admin_private_router.message.filter(OwnerFilter())


@admin_private_router.message(Command("admin"))
async def start(message: types.Message):
	await message.answer("Здраствуйте, чем займемся сегодня?", reply_markup=get_callback_btns(btns={
        '📃 Список товаров': 'products_list',
        '📃 Список категорий': 'categories_list',
        '➕ Добавить товар': 'add_product',
        '➕ Добавить категорию': 'add_catigory',
        '⚙ Настройки': 'settings'
    }, sizes=(2,2,1)))
	

# Получить список категорий
@admin_private_router.callback_query(F.data == 'categories_list')
async def choose_category(callback_query: types.CallbackQuery, session):
    await callback_query.answer()
    category_list = await orm_get_categories(session)

    for category in category_list:
        await callback_query.message.answer(
            text=f"<b>Имя:</b> {category.name}", 
            reply_markup=get_callback_btns(btns={'Изменить': f'editcategory_{category.id}', 'Удалить': f'deletecategory_{category.id}'})
        )


# Удаление категории
@admin_private_router.callback_query(F.data.startswith('deletecategory_'))
async def change_category_name(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer("Введите новое имя для категории:")
    await state.update_data(category_id=callback_query.data.split('_')[-1])
    await state.set_state(FSMEditCategory.name)


# Редактирование категории
class FSMEditCategory(StatesGroup):
    name = State()


@admin_private_router.callback_query(F.data.startswith('editcategory_'))
async def change_category_name(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer("Введите новое имя для категории:")
    await state.update_data(category_id=callback_query.data.split('_')[-1])
    await state.set_state(FSMEditCategory.name)


@admin_private_router.message(FSMEditCategory.name, F.text)
async def edit_category(message: types.Message, state: FSMContext, session):
    category_id = await state.get_data()
    await message.answer(f"✅ Название категории измененно на {message.text}")
    await orm_edit_category(session=session, category_id=category_id['category_id'], name=message.text)

    await state.clear()


# Получить список товара
@admin_private_router.callback_query(F.data == 'products_list')
async def choose_category(callback_query: types.CallbackQuery, session):
    await callback_query.answer()
    category_list = await orm_get_categories(session)

    await callback_query.message.answer(
        text='Выберите категорию:', 
        reply_markup=get_callback_btns(btns={str(i.name): 'category_'+str(i.id) for i in category_list})
    )


@admin_private_router.callback_query(F.data.startswith('category_'))
async def send_products_list(callback_query: types.CallbackQuery, session):
    await callback_query.answer()
    products_list = await orm_get_products(session, callback_query.data.split('_')[-1])

    for product in products_list:
        await callback_query.message.answer_photo(
            photo=product.image, 
            caption=f"<b>Имя:</b> {product.name}\n<b>Описание:</b> {product.description}\n\n<b>Цена:</b> {product.price}",
            reply_markup=get_callback_btns(btns={'Изменить': f'editproduct_{product.id}', 'Удалить': f'deleteproduct_{product.id}'})
            )

    await callback_query.message.answer("✅ Вот список товаров ⬆️")


# Удаление товара
@admin_private_router.callback_query(StateFilter('*'), F.data.startswith('deleteproduct_'))
async def delete_product(callback_query: types.CallbackQuery, session):
    await callback_query.answer()
    await orm_delete_product(session, callback_query.data.split('_')[-1])
    await callback_query.message.answer("✅ Товар удален")
    await callback_query.message.delete()


# Хендлер для отлова отмены FSM
@admin_private_router.message(StateFilter('*'), Command('отмена'))
async def CanselFSM(message: types.Message, state: FSMContext):
    currant_state = state.get_state()
    if currant_state == None:
        return
    
    await state.clear()
    await message.answer('❌ Действия отменены')


# FSM для добавления категория
class FSMAddCategory(StatesGroup):
    name = State()


@admin_private_router.callback_query(StateFilter(None), F.data == "add_catigory")
async def add_product(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите название категориии:')
    await state.set_state(FSMAddCategory.name)


@admin_private_router.message(FSMAddCategory.name, F.text)
async def add_product(message: types.Message, state: FSMContext, session):
    await message.answer('✅ Категория создана')
    await orm_create_categories(session=session, categories=[message.text])
    await state.clear()



# FSM для добавления товара
class FSMAddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    image = State()
    category_id = State()

    undo_text = {
		'FSMAddProduct:name': 'Введите название заного',
        'FSMAddProduct:description': 'Введите описание заного',
		'FSMAddProduct:price': 'Введите цену заного',
        'FSMAddProduct:image': 'Пришлите изображение заного',
        'FSMAddProduct:category_id': 'Выберите категорию заного',
    }


@admin_private_router.message(StateFilter('FSMAddProduct'), Command("назад"))
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    '''Шаг назад'''

    current_state = await state.get_state()

    if current_state == FSMAddProduct.name:
        await message.answer('Предидущего шага нет, или введите название товара или напишите "отмена"')
        return

    previous = None
    for step in FSMAddProduct.all_states:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок, вы вернулись к прошлому шагу \n {FSMAddProduct.undo_text[previous.state]}")
            return
        previous = step


@admin_private_router.callback_query(StateFilter(None), F.data == "add_product")
async def add_product(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('<b>Добавление товара</b>\nДля отмены пишите: /отмена \nЧтобы сделать шаг назад пишите: /назад \n\nВведите название товара:')
    await state.set_state(FSMAddProduct.name)


@admin_private_router.message(FSMAddProduct.name)
async def add_product_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Введите описание товара:')
    await state.set_state(FSMAddProduct.description)


@admin_private_router.message(FSMAddProduct.description)
async def add_product_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer('Введите цену товара:')
    await state.set_state(FSMAddProduct.price)


@admin_private_router.message(FSMAddProduct.price)
async def add_product_price(message: types.Message, state: FSMContext):
    try:
        await state.update_data(price=float(message.text))
        await message.answer('Пришлите изображение товара:')
        await state.set_state(FSMAddProduct.image)
    except:
         await message.answer("Вы ввели не число, попробуйте ещё раз:")


@admin_private_router.message(FSMAddProduct.image, F.photo)
async def add_product_image(message: types.Message, state: FSMContext, session):
    await state.update_data(image=message.photo[-1].file_id)
    categories = await orm_get_categories(session=session)
    await message.answer('Выберите категорию:', reply_markup=get_callback_btns(btns={str(i.name): str(i.id) for i in categories}))
    await state.set_state(FSMAddProduct.category_id)


@admin_private_router.callback_query(FSMAddProduct.category_id)
async def add_product_category(callback: types.CallbackQuery, state: FSMContext, session):
    await state.update_data(category=callback.data)
    await callback.answer()
    await callback.message.answer('✅ Товар создан')
    data = await state.get_data()
    await orm_add_product(session, data)
    await state.clear()




