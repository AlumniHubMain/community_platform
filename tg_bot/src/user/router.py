from aiogram import Router

from tg_bot.src.user.handlers.general import router as user_general_router


# Инициализируем и заполняем роутер уровня модуля
router: Router = Router()
router.include_router(user_general_router)
