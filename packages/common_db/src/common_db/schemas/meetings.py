from datetime import datetime
from pydantic import BaseModel, ConfigDict
from common_db.enums.meetings import EMeetingStatus, EMeetingUserRole, EMeetingResponseStatus
from common_db.schemas.base import BaseSchema, TimestampedSchema


class MeetingResponseRead(BaseSchema):
    user_id: int
    meeting_id: int
    role: EMeetingUserRole
    response: EMeetingResponseStatus | None = None
    created_at: datetime
    updated_at: datetime


class MeetingRead(TimestampedSchema):
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime
    status: EMeetingStatus
    user_responses: list[MeetingResponseRead]


class MeetingRequestCreate(BaseModel):
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime | None = None
    organizer_id: int


class MeetingRequestUpdate(BaseModel):
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime | None = None


# For user status in a meeting
class MeetingResponse(BaseModel):
    user_id: int
    role: EMeetingUserRole  # 'organizer', 'attendee'
    response: EMeetingResponseStatus | None = None  # 'confirmed', 'tentative', 'declined'

    model_config = ConfigDict(from_attributes=True)


class MeetingRequestRead(BaseModel):
    id: int
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime
    status: EMeetingStatus  # 'new', 'confirmed', 'archived'
    user_responses: list[MeetingResponse]  # List of users with their statuses

    model_config = ConfigDict(from_attributes=True)


class MeetingFilter(BaseModel):
    user_id: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class MeetingList(BaseModel):
    meetings: list[MeetingRequestRead]
