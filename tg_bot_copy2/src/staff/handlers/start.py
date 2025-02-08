from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from ..filters import IsStaff
from ..schemas import DTOTgBotStaffRead
from tg_bot.src.data.lexicon import LEXICON_RU
from tg_bot.src.logging.logging_report import info_logger
from tg_bot.src.logging.middleware import LoggingCommands, LoggingCallbacks


async def start_staff(message: Message, staff: DTOTgBotStaffRead):
    """
       Хэндлер для старта взаимодействия с ботом персонала alh
       """
    # checking the user's nickname
    if message.from_user.username is None:
        await message.answer(text=LEXICON_RU.get('no_username_on_start'))
        return

    # we save the utm tag if available
    str_param: str = ' '.join(message.text.split()[1:]) if len(message.text.split()) > 1 else None

    # we log the fact that the bot is started by the user in the local log and postgres
    info_logger.info(f'Сотрудник {staff.telegram_name} ({staff.name}) с id {staff.telegram_id} и ролью '
                     f'{staff.role.value} стартовал бота')

    # responding to the user
    await message.answer(text=LEXICON_RU['start_staff'] % (staff.appeal(), staff.role.value))


# Initialize and fill in the router of the module level
router: Router = Router()
router.message.filter(F.chat.type == "private")
router.message.middleware(LoggingCommands())
router.callback_query.middleware(LoggingCallbacks())

router.message.register(start_staff, CommandStart(), IsStaff())
