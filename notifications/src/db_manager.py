from sqlalchemy import select

from common_db.db_abstract import get_async_session
from .models import ORMUserProfile
from .schemas import DTONotifiedUserProfile


class NotificationManager:
    """Class containing methods for managing notification data"""

    @classmethod
    async def get_notified_user_profile(cls, user_id: int) -> DTONotifiedUserProfile | None:
        """Getting user notification settings from the database"""

        async for session in get_async_session():
            result = await session.execute(select(ORMUserProfile).filter(ORMUserProfile.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                return DTONotifiedUserProfile.model_validate(user, from_attributes=True)
            return None

        # TODO: если сведем модельки, то этот менеджер просто удалить
