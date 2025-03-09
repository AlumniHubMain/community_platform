from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common_db.config import schema
from common_db.models.base import ObjectTable

from ..enums.notifications import ENotificationType, NotificationTypePGEnum


class ORMUserNotifications(ObjectTable):
    """

    """

    __tablename__ = 'user_notifications'

    notification_type: Mapped[ENotificationType] = mapped_column(NotificationTypePGEnum)
    user_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.users.id'), index=True)
    params: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False)

    user: Mapped['ORMUserProfile'] = relationship(back_populates='notifications')

