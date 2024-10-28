from .handlers.start import router as staff_start_router
from aiogram import Router


# Инициализируем и заполняем роутер уровня модуля
router: Router = Router()
router.include_router(staff_start_router)
