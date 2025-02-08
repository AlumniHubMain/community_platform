from aiogram.filters import BaseFilter
from aiogram.types import Message

from tg_bot.src.user.schemas import DTOTgBotUser
from .crud_manager import StaffManager
from .models import TgBotStaffRole
from .schemas import DTOTgBotStaffRead, DTOTgBotStaffUpdate


class IsStaff(BaseFilter):
    """
    Фильтр для определения персонала бота. DTOTgBotStaffRead - если сотрудник, False - если нет.
    """

    async def __call__(self, message: Message) -> bool | dict[str, DTOTgBotStaffRead]:
        staff: DTOTgBotStaffRead | None = await StaffManager.get_staff(
            user=DTOTgBotUser(telegram_name=message.from_user.username, telegram_id=message.from_user.id))
        if staff is None:
            return False
        if staff.telegram_id is None:
            await StaffManager.update_staff(staff=DTOTgBotStaffUpdate(id=staff.id, telegram_id=message.from_user.id))
            staff.telegram_id = message.from_user.id
        return {'staff': staff}


class IsAdmin(BaseFilter):
    """
    Фильтр для определения админа бота. DTOTgBotStaffRead - если админ, False - если нет.
    """

    async def __call__(self, message: Message) -> bool | dict[str, DTOTgBotStaffRead]:
        staff: DTOTgBotStaffRead | None = await StaffManager.get_staff(
            user=DTOTgBotUser(telegram_name=message.from_user.username, telegram_id=message.from_user.id))
        if staff:
            if staff.role == TgBotStaffRole.admin:
                return {'admin': staff}
        return False
