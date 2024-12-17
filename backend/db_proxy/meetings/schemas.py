from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# For creating meeting requests
class MeetingRequestCreate(BaseModel):
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime | None = None
    organizer_id: int


# For reading meeting info
class MeetingRequestRead(BaseModel):
    id: int
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime
    status: str  # 'new', 'confirmed', 'archived'
    user_responses: list[MeetingResponse]  # List of users with their statuses

    class Config:
        from_attributes = True


class MeetingRequestUpdate(BaseModel):
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime | None = None


# For user status in a meeting
class MeetingResponse(BaseModel):
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
