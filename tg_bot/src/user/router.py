from .handlers.general import router as user_general_router
from aiogram import Router


# Инициализируем и заполняем роутер уровня модуля
router: Router = Router()
router.include_router(user_general_router)
