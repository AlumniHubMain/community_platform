from __future__ import annotations

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# For creating meeting requests
class MeetingRequestCreate(BaseModel):
    description: Optional[str] = None
    location: Optional[str] = None
    date: Optional[datetime] = None

    organiser_id: int

# For reading meeting requests
class SMeetingRequestRead(BaseModel):
    id: int
    description: Optional[str] = None
    location: Optional[str] = None
    scheduled_time: datetime
    status: str  # 'new', 'confirmed', 'archived'
    users: list[MeetingUserStatus]  # List of users with their statuses

    class Config:
        from_attributes = True

# For user status in a meeting
class MeetingUserStatus(BaseModel):
    user_id: int
    name: str
    role: str  # 'organizer', 'attendee'
    agreement: Optional[str] = None  # 'confirmed', 'tentative', 'declined'

    class Config:
        from_attributes = True
