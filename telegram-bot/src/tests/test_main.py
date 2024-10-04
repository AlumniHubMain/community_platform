import asyncio
import pytest
from unittest import mock
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, Message
from aiogram.enums import ParseMode
from ..main import get_secret, on_startup, init_bot, UserValidationMiddleware
from aiogram.types import Message, User, Chat
from datetime import datetime


@pytest.fixture
def mock_bot_and_dispatcher():
    with mock.patch.object(
        Bot, "__init__", return_value=None
    ) as mock_bot_init, mock.patch.object(Dispatcher, "__init__", return_value=None):
        bot_instance = Bot(token="test-token", parse_mode=ParseMode.HTML)
        dp_instance = Dispatcher()
        yield bot_instance, dp_instance


@pytest.mark.asyncio
async def test_on_startup(mock_bot_and_dispatcher):
    bot_instance, _ = mock_bot_and_dispatcher
    with mock.patch.object(bot_instance, "set_my_commands") as mock_set_commands:
        await on_startup(bot_instance)
        mock_set_commands.assert_called_once_with(
            [
                BotCommand(command="/survey", description="Пройти опрос"),
                BotCommand(
                    command="/view_profile", description="Посмотреть свою анкету"
                ),
                BotCommand(command="/start", description="Start the bot"),
                BotCommand(command="/help", description="Help information"),
            ]
        )


@pytest.mark.asyncio
async def test_user_validation_middleware(mock_bot_and_dispatcher):
    bot_instance, _ = mock_bot_and_dispatcher
    middleware = UserValidationMiddleware()

    user = User(id=12345, is_bot=False, first_name="TestUser")
    chat = Chat(id=1, type="private")

    message = Message(
        message_id=1,
        from_user=user,
        chat=chat,
        date=datetime.now(),
        text="Test message",
    )
    event = mock.Mock(message=message)

    mock_handler = mock.AsyncMock()

    with mock.patch.object(bot_instance, "send_message") as mock_send_message:
        await middleware(mock_handler, event, {})
        mock_send_message.assert_not_called()


@pytest.mark.asyncio
async def test_validate_user():
    middleware = UserValidationMiddleware()

    with mock.patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = mock.AsyncMock()
        mock_response.json.return_value = {"status": "success"}
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await middleware.validate_user(12345)
        assert result == {"status": "success"}
