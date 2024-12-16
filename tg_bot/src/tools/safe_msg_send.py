from aiogram.types import (BufferedInputFile, InlineKeyboardMarkup, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove, ForceReply)

from datetime import datetime

from tg_bot.src.loader import bot
from ..logging.crud_manager import LoggingManager
from ..logging.logging_report import report
from ..logging.schemas import DTOUpdateBlockedStatus


async def send(telegram_id: int,
               text: str,
               image: BufferedInputFile = None,
               reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply = None,
               parse_mode: str | None = None
               ) -> datetime | None:
    """
    A function for sending a message that verifies that the bot isn't banned by the user.

    telegram_id - telegram_id of the message recipient (you can send it only to the user who started the bot);
    body - message body;
    image - picture to the message (header), optional;
    reply_markup - keyboard, optional;
    parse_mode - format body (Markdown, HTML, etc.).

    Returns None if successful and the date the bot was blocked otherwise.
    """
    # checking the bot bun by the user
    response = await LoggingManager.is_user_blocked_bot(telegram_id=telegram_id)

    # if the ban date has returned from the database, we throw it higher
    if response:
        return response

    # we are trying to send a message to the user
    try:
        if image is None:
            await bot.send_message(chat_id=telegram_id,
                                   text=text,
                                   reply_markup=reply_markup,
                                   parse_mode=parse_mode)
        else:
            await bot.send_photo(chat_id=telegram_id,
                                 photo=image,
                                 caption=text,
                                 reply_markup=reply_markup,
                                 parse_mode=parse_mode)
        return None
    except Exception as e:
        # we assume that the person banned the bot, and we did not track it
        await report(description=f'I could not send a message to the user, '
                                 f'apparently he banned the bot, but we dont know\n'
                                 f'telegram_id: {telegram_id}\nmessage:\n{text}',
                     extent='error',
                     exception=e)

        # adding the fact of baning the bot to the database
        await LoggingManager.update_blocked_status(DTOUpdateBlockedStatus(telegram_id=telegram_id,
                                                                          is_blocked=True))

        # we are throwing today's date up
        return datetime.today()
