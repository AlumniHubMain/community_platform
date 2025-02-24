from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from typing import Callable, Awaitable

from .crud_manager import LoggingManager
from .models import TgBotEventType
from .schemas import DTOTgBotLoggingEvents


class LoggingCommands(BaseMiddleware):
    """
        Middleware, which logs the input of text commands in the bot.
        """

    async def __call__(
            self,
            handler: Callable[[Message, dict], Awaitable],
            event: Message,
            data: dict
    ):
        # event handling (message)
        result = await handler(event, data)

        # DTOTgBotLoggingEvents object with event parameters
        new_event: DTOTgBotLoggingEvents = DTOTgBotLoggingEvents(
            telegram_name=event.from_user.username,
            telegram_id=event.from_user.id,
            event_type=TgBotEventType.message,
            event_name=event.text,
            bot_state=None if data is None else ', '.join([x for x in data.values() if type(x) is str]),
            content=None,
            chat_title=event.chat.title,
            chat_id=event.chat.id)

        await LoggingManager.post_event(event=new_event)

        return result


class LoggingCallbacks(BaseMiddleware):
    """
        Middleware, which logs the triggering of callbacks in the bot.
        """

    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        # event handling (callback)
        result = await handler(event, data)

        # DTOTgBotLoggingEvents object with event parameters
        new_event: DTOTgBotLoggingEvents = DTOTgBotLoggingEvents(
            telegram_name=event.from_user.username,
            telegram_id=event.from_user.id,
            event_type=TgBotEventType.callback,
            event_name=event.text,
            bot_state=None if data is None else ', '.join([x for x in data.values() if type(x) is str]),
            content=None,
            chat_title=event.chat_instance,
            chat_id=event.message.chat.id)

        await LoggingManager.post_event(event=new_event)

        return result
