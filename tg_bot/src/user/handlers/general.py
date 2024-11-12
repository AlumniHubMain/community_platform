import requests as requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from tg_bot.src.logging.logging_report import info_logger


async def process_fox_command(message: Message):
    """
       Хэндлер для проверки работы бота и хорошего настроения
       """
    fox_response = requests.get('https://randomfox.ca/floof/')
    if fox_response.status_code == 200:
        fox_link = fox_response.json()['image']
        await message.answer_photo(fox_link)
    else:
        await message.answer('🦊')
    info_logger.info(f'Пользователь {message.from_user.username} с id {message.from_user.id} использовал fox')


# Инициализируем и заполняем роутер уровня модуля
router: Router = Router()

router.message.register(process_fox_command, Command(commands='fox', ignore_case=True))
