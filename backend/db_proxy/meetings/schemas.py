from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# For creating meeting requests
class MeetingRequestCreate(BaseModel):
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime | None = None

    organizer_id: int


# For reading meeting requests
class MeetingRequestRead(BaseModel):
    id: int
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime
    status: str  # 'new', 'confirmed', 'archived'
    user_responses: list[MeetingUserStatus]  # List of users with their statuses

    class Config:
        from_attributes = True


class MeetingUserInfo(BaseModel):
    id: int
    name: str
    surname: str
    email: str
    # ToDo: add fields required in the frontend
    # ToDo: This is probably some more generic "UserCard"

# For user status in a meeting
class MeetingUserStatus(BaseModel):
    user_id: int
    role: str  # 'organizer', 'attendee'
    response: str | None = None  # 'confirmed', 'tentative', 'declined'

    class Config:
        from_attributes = True


# filter for user's meeting searches
class MeetingFilter(BaseModel):
    user_id: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class MeetingList(BaseModel):
    meetings: list[MeetingRequestRead]
