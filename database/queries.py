import math
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Tariff, User, Admin


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


async def orm_add_tariff(session: AsyncSession, data: dict):
    obj = Tariff(
        name=data["name"],
        sub_time=data["sub_time"],
        price=float(data["price"]),
    )
    session.add(obj)
    await session.commit()


async def orm_get_tariff(session: AsyncSession, tariff_id: int):
    query = select(Tariff).where(Tariff.id == tariff_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_delete_tariff(session: AsyncSession, tariff_id: int):
    
    query = delete(Tariff).where(Tariff.id == tariff_id)
    await session.execute(query)
    await session.commit()


# Добавление пользователя
async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    name: str | None = None,
) -> None:
    '''Добавляет пользователя если его нет
    '''
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            User(user_id=user_id, name=name, status=0)
        )
        await session.commit()


async def orm_change_user_status(session: AsyncSession, user_id, new_status, sub_time, tun_id):
    
    query = update(User).where(User.id == user_id).values(
            status=new_status,
            sub_time=sub_time,
            tun_id=tun_id
        )
    await session.execute(query)
    await session.commit()


async def orm_get_users(session: AsyncSession):
    '''Возвращает список пользвателей
    
    session: Ассинхроная сессия sqlalchemy
    '''
    query = select(User)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_blocked_users(session: AsyncSession):
    '''Возвращает список пользвателей
    
    session: Ассинхроная сессия sqlalchemy
    '''
    query = select(User).where(User.blocked == True)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_user(session: AsyncSession, user_id: int):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    return result.scalar()


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

