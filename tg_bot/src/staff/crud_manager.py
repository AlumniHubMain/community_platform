from sqlalchemy import or_, update, func
from sqlalchemy.future import select

from tg_bot.src.user.schemas import DTOTgBotUser
from .models import ORMTgBotStaff
from .schemas import DTOTgBotStaffRead, DTOTgBotStaffUpdate
from common_db.db_abstract import get_async_session


class StaffManager:
    """
    Класс, содержащий методы для управления данными персонала alh, взаимодействующего с ботом
    """

    @classmethod
    async def get_staff(cls, user: DTOTgBotUser) -> DTOTgBotStaffRead | None:
        """
        Метод, возвращающий объект DTOTgBotStaffRead по telegram_name/telegram_id
        """
        async for session in get_async_session():
            result = await session.execute(select(ORMTgBotStaff).
                                           filter(or_(func.lower(ORMTgBotStaff.telegram_name) == user.telegram_name,
                                                      ORMTgBotStaff.telegram_id == user.telegram_id)
                                                  )
                                           )
            staff = result.scalar_one_or_none()
            if staff:
                return DTOTgBotStaffRead.model_validate(staff)
            return None

    @classmethod
    async def update_staff(cls, staff: DTOTgBotStaffUpdate):
        """
        Метод, обновляющий данные персонала в базе
        """
        async for session in get_async_session():
            await session.execute(update(ORMTgBotStaff)
                                  .where(ORMTgBotStaff.id == staff.id)
                                  .values(**staff.model_dump(exclude_unset=True, exclude_none=True)))

            await session.commit()
