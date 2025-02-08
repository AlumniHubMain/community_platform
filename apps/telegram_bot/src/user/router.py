from aiogram import Router

from .handlers.general import router as user_general_router
from .handlers.other import router as user_other_router


# Initialize and fill in the router of the module level
router: Router = Router()
router.include_router(user_general_router)
router.include_router(user_other_router)
