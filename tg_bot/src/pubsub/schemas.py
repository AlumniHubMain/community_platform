from datetime import datetime
from pydantic import BaseModel


class DTONotifiedUserProfile(BaseModel):
    """The scheme of the notified use"""
    name: str
    surname: str
    email: str
    linkedin_link: str | None = None
    telegram_name: str | None = None
    telegram_id: int | None = None
    current_company: str | None = None


class DTONotificationMessage(BaseModel):
    """The scheme of the prepared notification"""
    user_id: int
    type: str
    text: str
    timestamp: datetime | None
    user: DTONotifiedUserProfile
