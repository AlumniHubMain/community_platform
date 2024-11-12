from sqlalchemy import update

from .models import ORMTgBotLoggingEvents
from .schemas import DTOTgBotLoggingEvents, DTOUpdateBlockedStatus
from backend.db_proxy.common_db.db_abstract import get_async_session
from backend.db_proxy.common_db.models import ORMUserProfile


class LoggingManager:
    """
    Класс, содержащий методы для управления данными логирования взаимодействий с ботом
    """

    @classmethod
    async def post_event(cls, event: DTOTgBotLoggingEvents) -> int:
        """
        Метод, сохраняющий информацию по ивенту в соответствующую таблицу БД
        """
        async for session in get_async_session():
            new_event = ORMTgBotLoggingEvents(**event.model_dump())
            session.add(new_event)
            await session.flush()
            await session.commit()
            return new_event.id

    @classmethod
    async def update_blocked_status(cls, event: DTOUpdateBlockedStatus) -> None:
        """
        Метод, обновляющий статус блокировки бота человеком в таблице users
        """
        async for session in get_async_session():
            await session.execute(update(ORMUserProfile)
                                  .where(ORMUserProfile.telegram_id == event.telegram_id)
                                  .values(is_tg_bot_blocked=event.is_blocked,
                                          blocked_status_update_date=event.status_update_date))
            await session.commit()
