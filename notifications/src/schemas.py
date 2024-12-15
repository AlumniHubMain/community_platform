from datetime import datetime, UTC


from pydantic import BaseModel
from pydantic_extra_types.timezone_name import TimeZoneName


class DTONotificationMessage(BaseModel):
    """Incoming notification scheme"""
    user_id: int
    type: str
    text: str
    timestamp: datetime | None


class DTONotificationSettings(BaseModel):
    """User notification settings scheme"""
    timezone: TimeZoneName | None = None
    is_tg_notify: bool | None = None
    is_email_notify: bool | None = None
    is_telephone_notify: bool | None = None


class DTOPreparedNotification(DTONotificationMessage):
    """The scheme of the prepared notification"""
    settings: DTONotificationSettings | None
    timestamp: datetime = datetime.now(UTC)
