from aiogram.filters import BaseFilter
from aiogram.types import Message

from .crud_manager import UserManager
from .schemas import DTOTgBotUser, DTOTgBotUserUpdate, DTOTgBotUserRead


class IsUserRegistered(BaseFilter):
    """
    Фильтр для определения есть ли пользователь с таким ником/id в БД. DTOTgBotUserRead - если есть, False - если нет.
    """

    async def __call__(self, message: Message) -> bool | dict[str, DTOTgBotUserRead]:
        user: DTOTgBotUserRead | None = await UserManager.get_user(
            user=DTOTgBotUser(telegram_name=message.from_user.username, telegram_id=message.from_user.id))
        if user is None:
            return False
        if user.telegram_id is None:
            await UserManager.update_user(user=DTOTgBotUserUpdate(id=user.id, telegram_id=message.from_user.id))
            user.telegram_id = message.from_user.id
        return {'user': user}
