from datetime import datetime, UTC

from pydantic import BaseModel, Field, EmailStr
from pydantic_extra_types.timezone_name import TimeZoneName


class DTONotificationMessage(BaseModel):
    """Incoming notification scheme"""
    user_id: int
    type: str
    head: str | None = None
    body: str | None = None
    timestamp: datetime | None


class DTONotifiedUserProfile(BaseModel):
    """The scheme of the notified use"""
    name: str
    surname: str
    email: EmailStr
    linkedin_link: str | None = None
    telegram_name: str | None = None
    telegram_id: int | None = None
    is_tg_bot_blocked: bool | None = Field(default=None, exclude=True)
    timezone: TimeZoneName | None = Field(default=None, exclude=True)
    is_tg_notify: bool | None = Field(default=None, exclude=True)
    is_email_notify: bool | None = Field(default=None, exclude=True)
    is_push_notify: bool | None = Field(default=None, exclude=True)


class DTOPreparedNotification(DTONotificationMessage):
    """The scheme of the prepared notification"""
    user: DTONotifiedUserProfile
    timestamp: datetime = datetime.now(UTC)
