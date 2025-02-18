import asyncio

from aiogram.types import BotCommand

from src.config import settings
from src.loader import dp, bot, broker
from src.logging.logging_report import report
from src.message_broker.incoming_message import message_handler
from src.staff.router import router as staff_router
from src.user.router import router as user_router


async def on_startup():
    print('Бот вышел в онлайн')
    await report('Бот вышел в онлайн')

    # Create a list with commands and their descriptions for the menu button
    main_menu_commands = [
        BotCommand(command='/fox', description='🦊'),
    ]
    await bot.set_my_commands(main_menu_commands)

    # subscribing to the tg_notification topic of message broker in background task
    asyncio.create_task(broker.subscribe(settings.ps_notification_tg_sub_name, message_handler))


async def main():
    # Register the routers in the dispatcher
    dp.include_router(staff_router)
    dp.include_router(user_router)

    print('Бот запущен')

    # Skip the accumulated updates and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    dp.startup.register(on_startup)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
