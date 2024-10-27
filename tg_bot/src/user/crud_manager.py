from .schemas import DTOTgBotUser, DTOTgBotUserUpdate, DTOTgBotUserRead
from backend.db_proxy.common_db.models import ORMUserProfile
from backend.db_proxy.common_db.db_abstract import get_async_session
from sqlalchemy import or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class UserManager:
    """
    Класс, содержащий методы для управления данными пользователей
    """

    @classmethod
    async def get_user(cls, user: DTOTgBotUser) -> DTOTgBotUserRead | None:
        """
        Метод, возвращающий объект DTOTgBotUserRead по telegram_name/telegram_id
        """
        async for session in get_async_session():
            result = await session.execute(select(ORMUserProfile).
                                           filter(or_(ORMUserProfile.telegram_name == user.telegram_name,
                                                      ORMUserProfile.telegram_id == user.telegram_id)
                                                  )
                                           )
            user = result.scalar_one_or_none()
            if user:
                return DTOTgBotUserRead.model_validate(user)
            return None

    @classmethod
    async def update_user(cls, user: DTOTgBotUserUpdate):
        """
        Метод, обновляющий данные пользователя в базе
        """
        async for session in get_async_session():
            await session.execute(update(ORMUserProfile)
                                  .where(ORMUserProfile.id == user.id)
                                  .values(**user.model_dump(exclude_unset=True, exclude_none=True)))

            await session.commit()
