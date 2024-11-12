from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from ..filters import IsStaff
from ..schemas import DTOTgBotStaffRead
from tg_bot.src.data.lexicon import LEXICON_RU
from tg_bot.src.logging.logging_report import info_logger


async def start_staff(message: Message, staff: DTOTgBotStaffRead):
    """
       Хэндлер для старта взаимодействия с ботом персонала alh
       """
    # проверка наличия ника у пользователя
    if message.from_user.username is None:
        await message.answer(text=LEXICON_RU.get('no_username_on_start'))
        return

    # сохраняем utm-метку при наличии
    str_param: str = ' '.join(message.text.split()[1:]) if len(message.text.split()) > 1 else None

    # логируем факт старта бота пользователем в локальный лог и postgres
    info_logger.info(f'Сотрудник {staff.telegram_name} ({staff.name}) с id {staff.telegram_id} и ролью '
                     f'{staff.role.value} стартовал бота')

    # отвечаем пользователю
    await message.answer(text=LEXICON_RU['start_staff'] % (staff.appeal(), staff.role.value))


# Инициализируем и заполняем роутер уровня модуля
router: Router = Router()
router.message.filter(F.chat.type == "private")

router.message.register(start_staff, CommandStart(), IsStaff())
