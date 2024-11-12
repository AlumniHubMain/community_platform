from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from typing import Callable, Dict, Any, Awaitable

from .crud_manager import LoggingManager
from .logging_report import report
from .models import TgBotEventType
from .schemas import DTOTgBotLoggingEvents


class LoggingCommands(BaseMiddleware):
    """
            Мидлвари, логирующий ввод текстовых команд в боте.
            """

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # обработка события (message)
        result = await handler(event, data)

        # объект DTOTgBotLoggingEvents с параметрами ивента
        new_event: DTOTgBotLoggingEvents = DTOTgBotLoggingEvents(
            telegram_name=event.from_user.username,
            telegram_id=event.from_user.id,
            event_type=TgBotEventType.message,
            event_name=event.text,
            bot_state=None if data is None else ', '.join([x for x in data.values() if type(x) is str]),
            content=None,
            chat_title=event.chat.title,
            chat_id=event.chat.id)

        try:
            await LoggingManager.post_event(event=new_event)
        except Exception as e:
            await report(description=f'Ошибка при записи в базу ивента (message) {new_event.event_name}\n'
                                     f'username: {new_event.telegram_name}\nid: {new_event.telegram_id}\n'
                                     f'chat title: {new_event.chat_title}\nchat id: {new_event.chat_id}\n'
                                     f'bot state: {new_event.bot_state}',
                         extent='error',
                         exception=e)

        return result


class LoggingCallbacks(BaseMiddleware):
    """
            Мидлвари, логирующий срабатывание колбэков в боте.
            """

    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        # обработка события (callback)
        result = await handler(event, data)

        # объект DTOTgBotLoggingEvents с параметрами ивента
        new_event: DTOTgBotLoggingEvents = DTOTgBotLoggingEvents(
            telegram_name=event.from_user.username,
            telegram_id=event.from_user.id,
            event_type=TgBotEventType.callback,
            event_name=event.text,
            bot_state=None if data is None else ', '.join([x for x in data.values() if type(x) is str]),
            content=None,
            chat_title=event.chat_instance,
            chat_id=event.message.chat.id)

        try:
            await LoggingManager.post_event(event=new_event)
        except Exception as e:
            await report(description=f'Ошибка при записи в базу ивента (callback) {new_event.event_name}\n'
                                     f'username: {new_event.telegram_name}\nid: {new_event.telegram_id}\n'
                                     f'chat title: {new_event.chat_title}\nchat id: {new_event.chat_id}\n'
                                     f'bot state: {new_event.bot_state}',
                         extent='error',
                         exception=e)

        return result
