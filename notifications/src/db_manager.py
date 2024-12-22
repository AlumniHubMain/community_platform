from sqlalchemy import select
from sqlalchemy.orm import joinedload

from backend.db_proxy.common_db.db_abstract import get_async_session
from backend.db_proxy.common_db.user_model import ORMUserProfile
from .models import ORMNotificationSettings
from .schemas import DTONotificationSettings, DTONotifiedUserProfile


class NotificationManager:
    """Class containing methods for managing notification data"""

    @classmethod
    async def get_user_notification_settings(cls, user_id: int) -> DTONotificationSettings | None:
        """Getting user notification settings from the database"""

        async for session in get_async_session():
            result = await session.execute(select(ORMNotificationSettings)
                                           .where(ORMNotificationSettings.user_id == user_id))
            settings = result.scalar_one_or_none()
            if settings:
                return DTONotificationSettings.model_validate(settings)
            return None

    @classmethod
    async def get_notified_user_profile(cls, user_id: int) -> DTONotificationSettings | None:
        """Getting user notification settings from the database"""

        async for session in get_async_session():
            result = await session.execute(select(ORMUserProfile)
                                           .filter(ORMUserProfile.id == user_id)
                                           .options(joinedload(ORMUserProfile.notification_settings)))
            settings = result.scalar_one_or_none()
            if settings:
                return DTONotifiedUserProfile.model_validate(settings)
            return None

        # TODO: если сведем модельки, то этот менеджер просто удалить
