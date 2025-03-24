from enum import Enum
from sqlalchemy import Enum as PGEnum


class ENotificationType(Enum):
    """The enum containing notification types"""
    user_test: str = 'user_test'
    meeting_invitation: str = 'meeting_invitation'


NotificationTypePGEnum = PGEnum(ENotificationType, name='notification_type', inherit_schema=True)
