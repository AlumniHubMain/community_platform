from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ORMNotificationSettings
from ..schemas import DTONotificationSettings
from backend.db_proxy.common_db.db_abstract import get_async_session


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
