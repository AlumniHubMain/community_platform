from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI
from google.cloud import secretmanager
from aiogram import Bot, Dispatcher, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand, Update
from aiogram import BaseMiddleware
import time


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


def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    project_id = "communityp"
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode("UTF-8")


TOKEN = os.getenv("BOT_TOKEN") or get_secret("telegram-bot-token")

WEBHOOK_URL = os.getenv("CLOUD_RUN_URL") + "/webhook"

logging.basicConfig(filemode="a", level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)


dp.update.outer_middleware(UserValidationMiddleware())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(WEBHOOK_URL)
    main_menu_commands = [
        BotCommand(command="/survey", description="Пройти опрос"),
        BotCommand(command="/view_profile", description="Посмотреть свою анкету"),
        BotCommand(command="/start", description="Start the bot"),
        BotCommand(command="/help", description="Help information"),
    ]
    await bot.set_my_commands(main_menu_commands)
    yield

    await bot.delete_webhook()
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


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



@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(
        f"Start: {user_id} {user_full_name} {time.asctime()}. Message: {message}"
    )
    await message.reply(f"Hello, {user_full_name}!")



@app.post("/webhook")
async def bot_webhook(update: dict):
    await dp.feed_webhook_update(bot=bot, update=Update(**update))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
