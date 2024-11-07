from aiogram import Router

from tg_bot.src.staff.handlers.start import router as staff_start_router


# Инициализируем и заполняем роутер уровня модуля
router: Router = Router()
router.include_router(staff_start_router)
