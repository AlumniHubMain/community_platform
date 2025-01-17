from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from common_db.enums.meetings import EMeetingUserRole, EMeetingResponseStatus, EMeetingStatus


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
    status: EMeetingStatus
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
    role: EMeetingUserRole
    response: EMeetingResponseStatus | None = None

    class Config:
        from_attributes = True


# filter for user's meeting searches
class MeetingFilter(BaseModel):
    user_id: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class MeetingList(BaseModel):
    meetings: list[MeetingRequestRead]


class MeetingsUserLimits(BaseModel):
    
    # Meetings pendings limit for user
    meetings_pendings_limit: int = 0
    
    # Meetings confirmations limit for user
    meetings_confirmations_limit: int = 0
    
    # Count of available meeting pendings for user
    available_meeting_pendings: int = 0

    # Count of available meetings confirmations for user
    available_meeting_confirmations: int = 0
