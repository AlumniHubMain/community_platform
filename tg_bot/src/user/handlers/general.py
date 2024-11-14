import requests as requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from tg_bot.src.logging.logging_report import info_logger
from tg_bot.src.logging.middleware import LoggingCommands, LoggingCallbacks


async def process_fox_command(message: Message):
    """
       Handler for checking the bot's performance and good mood
       """
    fox_response = requests.get('https://randomfox.ca/floof/')
    if fox_response.status_code == 200:
        fox_link = fox_response.json()['image']
        await message.answer_photo(fox_link)
    else:
        await message.answer('🦊')
    info_logger.info(f'user {message.from_user.username} with id {message.from_user.id} used /fox')


# Initialize and fill in the router of the module level
router: Router = Router()
router.message.middleware(LoggingCommands())
router.callback_query.middleware(LoggingCallbacks())

router.message.register(process_fox_command, Command(commands='fox', ignore_case=True))
