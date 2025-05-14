from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from kbds.inline import get_callback_btns
from filters.users_filter import OwnerFilter
from database.queries import orm_add_product, orm_create_categories

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
    await message.answer('Категории')
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


@admin_private_router.callback_query(StateFilter(None), F.data == "add_product")
async def add_product(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите название товара:')
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
async def add_product_image(message: types.Message, state: FSMContext):
    await state.update_data(image=message.photo[-1].file_id)
    await message.answer('Введите цену товара:')
    await state.set_state(FSMAddProduct.category_id)


@admin_private_router.callback_query(FSMAddProduct.category_id)
async def add_product_category(callback: types.CallbackQuery, state: FSMContext, session):
    await state.update_data(category=callback.message.text)
    await callback.answer()
    await callback.message.answer('Товар создан')
    data = await state.get_data()
    await orm_add_product(session, data)
    await state.clear()




