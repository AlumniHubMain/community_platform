import asyncio

from aiogram.types import BotCommand

from src.loader import dp, bot
from src.logging.logging_report import report
from src.staff.router import router as staff_router
from src.user.router import router as user_router


async def on_startup():
    print('Бот вышел в онлайн')
    await report('Бот вышел в онлайн')

    # Создаем список с командами и их описанием для кнопки menu
    main_menu_commands = [
        BotCommand(command='/fox', description='🦊'),
    ]
    await bot.set_my_commands(main_menu_commands)


async def main():
    # Регистрируем роутеры в диспетчере
    dp.include_router(staff_router)
    dp.include_router(user_router)

    print('Бот запущен')

    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    dp.startup.register(on_startup)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
