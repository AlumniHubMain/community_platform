from .config import settings
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler


bot = Bot(token=settings.bot_token.get_secret_value())
dp: Dispatcher = Dispatcher()

scheduler = AsyncIOScheduler()  # объект асинхронного шедуллера
