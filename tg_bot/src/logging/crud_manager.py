from datetime import datetime

from sqlalchemy import update, select

from .logging_report import report
from .models import ORMTgBotLoggingEvents
from .schemas import DTOTgBotLoggingEvents, DTOUpdateBlockedStatus, DTOCheckUserBlockedBot
from common_db.db_abstract import get_async_session
from common_db.user_model import ORMUserProfile


class LoggingManager:
    """
    A class containing methods for managing data logging interactions with a bot.
    """

    @classmethod
    async def post_event(cls, event: DTOTgBotLoggingEvents) -> int:
        """
        A method that stores information about the event in the corresponding database table.
        """
        try:
            async for session in get_async_session():
                new_event = ORMTgBotLoggingEvents(**event.model_dump())
                session.add(new_event)
                await session.flush()
                await session.commit()
                return new_event.id
        except Exception as e:
            await report(description=f'Error when writing event to the database ({event.event_type}) '
                                     f'{event.event_name}\n'
                                     f'username: {event.telegram_name}\nid: {event.telegram_id}\n'
                                     f'chat title: {event.chat_title}\nchat id: {event.chat_id}\n'
                                     f'bot state: {event.bot_state}',
                         extent='error',
                         exception=e)

    @classmethod
    async def update_blocked_status(cls, event: DTOUpdateBlockedStatus) -> None:
        """
        A method that updates the status of the bot baning by a person in the users table.
        """
        try:
            async for session in get_async_session():
                await session.execute(update(ORMUserProfile)
                                      .where(ORMUserProfile.telegram_id == event.telegram_id)
                                      .values(is_tg_bot_blocked=event.is_blocked,
                                              blocked_status_update_date=event.status_update_date))
                await session.commit()
        except Exception as e:
            await report(description=f'Error when updating the bots blocking status\n'
                                     f'username: {event.from_user.username}\n'
                                     f'id: {event.from_user.id}\n'
                                     f'is blocked: {event.is_blocked}\n',
                         extent='error',
                         exception=e)

    @classmethod
    async def is_user_blocked_bot(cls, telegram_id: int) -> datetime | None:
        """
        A method that checks if a bot is banned by a human.
        Returns the baning date if the bot is banned or None otherwise.
        """
        try:
            async for session in get_async_session():
                result = await session.execute(select(ORMUserProfile)
                                               .where(ORMUserProfile.telegram_id == telegram_id))
                user = DTOCheckUserBlockedBot.model_validate(result.scalar_one_or_none())

                if user.is_tg_bot_blocked:
                    return user.blocked_status_update_date

        except Exception as e:
            await report(description=f'Error checking the bot ban\n'
                                     f'telegram_id: {telegram_id}\n',
                         extent='error',
                         exception=e)
