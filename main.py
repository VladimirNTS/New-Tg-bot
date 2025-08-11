import hashlib
import logging
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()
from aiogram.types import Update
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot import bot, dp
from database.engine import session
from database.queries import (
    orm_get_user,
    orm_get_tariff,
    get_last_payment_id,
    orm_get_product
)


async def get_session(
    session_pool: async_sessionmaker,
):
    async with session_pool() as session:
        return session
    



@asynccontextmanager
async def lifespan(app: FastAPI):
    url_webhook = f'{os.getenv("PAY_PAGE_URL")}/bot_webhook'
    await bot.set_webhook(url=url_webhook,
                          allowed_updates=dp.resolve_used_update_types(),
                          drop_pending_updates=True)
    yield
    await bot.delete_webhook()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/new_subscribe", response_class=HTMLResponse)
async def subscribe(
    request: Request,
    user_id: int,
    sub_id: int
):
    async_session = await get_session(session_pool=session)

    user = await orm_get_user(async_session, user_id=user_id)
    tariff = await orm_get_tariff(async_session, tariff_id=sub_id)

    base_string = f"{os.getenv('SHOP_ID')}:{tariff.price}::{os.getenv('PASSWORD_1')}"
    signature_value = hashlib.md5(base_string.encode("utf-8")).hexdigest()
    invoice_id = await get_last_payment_id(async_session)

    return templates.TemplateResponse("/pay_new_subscribe.html", {"request": request, "price": tariff.price, "shop_id": os.getenv("SHOP_ID"), "signature_value": signature_value, "invoice_id": invoice_id})


@app.get("/new_order", response_class=HTMLResponse)
async def buy(
    request: Request,
    user_id: int,
    sub_id: int
):
    async_session = await get_session(session_pool=session)

    user = await orm_get_user(async_session, user_id=user_id)
    tariff = await orm_get_product(async_session, product_id=sub_id)

    invoice_id = await get_last_payment_id(async_session) + 1
    base_string = f"{os.getenv('SHOP_ID')}:{tariff.price}:{invoice_id}:{os.getenv('PASSWORD_1')}"
    signature_value = hashlib.md5(base_string.encode("utf-8")).hexdigest()
    print(f"{os.getenv('SHOP_ID')}:{tariff.price}:{invoice_id}:{os.getenv('PASSWORD_1')}")
    return templates.TemplateResponse("/buy_one_time.html", {"request": request, "price": tariff.price, "shop_id": os.getenv("SHOP_ID"), "signature_value": signature_value, "invoice_id": invoice_id, "time": tariff.price})



@app.post("/bot_webhook")
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )

    uvicorn.run(app, host="localhost", port=5000)
