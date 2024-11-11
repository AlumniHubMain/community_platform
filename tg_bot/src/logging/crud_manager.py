from sqlalchemy import or_, update, func
from sqlalchemy.future import select

from .models import ORMTgBotLoggingEvents
from .schemas import DTOTgBotLoggingEvents
from backend.db_proxy.common_db.db_abstract import get_async_session


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
