from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import settings


bot = Bot(token=settings.bot_token.get_secret_value())
dp: Dispatcher = Dispatcher()

scheduler = AsyncIOScheduler()  # объект асинхронного шедуллера
