import math
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from databare.models import Tariff, User, Admin


# Tariffs
async def orm_get_tariffs(session: AsyncSession):
    '''Возвращает список тарифов
    
    session: Ассинхроная сессия sqlalchemy
    '''
    query = select(Tariff)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_edit_tariff(session: AsyncSession, tariff_id, name, sub_time, price):
    
    query = update(Tariff).where(Tariff.id == tariff_id).values(
            name=name,
            sub_time=sub_time,
            price=price
        )
    await session.execute(query)
    await session.commit()


# Админка: добавить/изменить/удалить товар
async def orm_add_product(session: AsyncSession, data: dict):
    '''Создание нового продукта в базе данных
    
    session: Ассинхроная сессия sqlalchemy
    data: даннае необходимые для создания товара {name, description, price, image, category}
    '''
    obj = Product(
        name=data["name"],
        description=data["description"],
        price=float(data["price"]),
        image=data["image"],
        category_id=int(data["category"]),
    )
    session.add(obj)
    await session.commit()


async def orm_get_products(session: AsyncSession, category_id):
    '''Возвращает все товары из базы по id категории
    
    session: Ассинхроная сессия sqlalchemy
    category_id: Айди категории с товарами
    '''
    query = select(Product).where(Product.category_id == int(category_id))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_product(session: AsyncSession, product_id: int):
    '''Возвращает товар из базы по id товара
    
    session: Ассинхроная сессия sqlalchemy
    product_id: Айди товара
    '''
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_product(session: AsyncSession, product_id: int, data):
    '''Изменяет товар по его id
    
    session: Ассинхроная сессия sqlalchemy
    product_id: Айди товара
    data: Новые данные для товара
    '''
    query = (
        update(Product)
        .where(Product.id == product_id)
        .values(
            name=data["name"],
            description=data["description"],
            price=float(data["price"]),
            image=data["image"],
            category_id=int(data["category"]),
        )
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_product(session: AsyncSession, product_id: int):
    
    query = delete(Product).where(Product.id == product_id)
    await session.execute(query)
    await session.commit()


# Добавление пользователя
async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
) -> None:
    '''Добавляет пользователя если его нет
    '''
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            User(user_id=user_id, first_name=first_name, last_name=last_name, phone=phone)
        )
        await session.commit()


# Корзина
async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int) -> tuple:
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id).options(joinedload(Cart.product))
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:
        cart.quantity += 1
        await session.commit()
        return cart
    else:
        session.add(Cart(user_id=user_id, product_id=product_id, quantity=1))
        await session.commit()



async def orm_get_user_carts(session: AsyncSession, user_id):
    query = select(Cart).filter(Cart.user_id == user_id).options(joinedload(Cart.product))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_id: int):
    query = delete(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    await session.execute(query)
    await session.commit()


async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id).options(joinedload(Cart.product))
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:
        return
    if cart.quantity > 1:
        cart.quantity -= 1
        await session.commit()
        return True
    else:
        await orm_delete_from_cart(session, user_id, product_id)
        await session.commit()
        return False


# Работа с администраторами
async def orm_add_admin(session, user_id):
    '''Добавить нового администратора в таблицу'''
    session.add(
        Admin(
            user_id=user_id
        )
    )
    await session.commit()


async def orm_delete_admin(session, user_id):
    '''Удалить администратора из таблицы'''
    query = delete(Admin).where(user_id==user_id)
    await session.execute(query)
    await session.commit()

