import asyncio
import logging
from os import getenv
import sys
from google.cloud import secretmanager
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand
import aiohttp
from aiogram import BaseMiddleware
from aiogram.types import Message

dp = Dispatcher()


class UserValidationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = None

        if hasattr(event, "message") and event.message is not None:
            user_id = event.message.from_user.id
        elif hasattr(event, "callback_query") and event.callback_query is not None:
            user_id = event.callback_query.from_user.id

        if user_id is not None:
            validation_result = await self.validate_user(user_id)

            if validation_result["status"] == "in_progress":
                await bot.send_message(
                    user_id,
                    "Подождите пока ваша анкета будет активирована, это занимает примерно Х",
                )
                return
            elif validation_result["status"] == "survey_required":
                await bot.send_message(user_id, "Необходимо заполнить анкету")
                return
            elif validation_result["status"] == "denied":
                await bot.send_message(user_id, "У вас нет доступа")
                return

        return await handler(event, data)

    async def validate_user(self, user_id: int):
        return {"status": "success"}
        # async with aiohttp.ClientSession() as session:
        #     validation_url = ""
        #     data = {'user_id': user_id}
        #     async with session.post(validation_url, data) as response:
        #         return await response.json()


dp.update.outer_middleware(UserValidationMiddleware())


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message(Command("survey"))
async def survey_handler(message: Message) -> None:
    # Логика опроса
    # async with aiohttp.ClientSession() as session:
    #         register_url = ""
    #         data = {'survey_results': survey_results}
    #         async with session.post(register_url, data) as response:
    #             return await response.json()
    ...


def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    project_id = ""
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

    response = client.access_secret_version(request={"name": secret_name})
    secret_value = response.payload.data.decode("UTF-8")

    return secret_value


def init_bot():
    TOKEN = getenv("BOT_TOKEN")

    if not TOKEN:
        logging.info(
            "BOT_TOKEN not found in environment, loading from Google Secret Manager..."
        )
        TOKEN = get_secret("telegram-bot-token")

    return Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

async def on_startup(bot: Bot) -> None:
    main_menu_commands = [
        BotCommand(command="/survey", description="Пройти опрос"),
        BotCommand(command="/view_profile", description="Посмотреть свою анкету"),
        BotCommand(command="/start", description="Start the bot"),
        BotCommand(command="/help", description="Help information"),
    ]
    await bot.set_my_commands(main_menu_commands)


async def main() -> None:

    bot = init_bot()
    await on_startup(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
