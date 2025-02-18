from datetime import datetime
from pydantic import BaseModel, ConfigDict
from common_db.enums.meetings import EMeetingStatus, EMeetingUserRole, EMeetingResponseStatus, EMeetingLocation
from common_db.schemas.base import BaseSchema, TimestampedSchema


class MeetingResponseRead(BaseSchema):
    user_id: int
#    meeting_id: int
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
    organizer_id: int
    match_id: int | None = None
    attendees_id: list[int]
    scheduled_time: datetime | None = None
    location: EMeetingLocation
    description: str | None = None


class MeetingRequestUpdate(BaseModel):
    description: str | None = None
    location: EMeetingLocation | None = None
    scheduled_time: datetime | None = None
    
    @staticmethod
    def get_update_rules():
        # Default:
        #   permission: [organizer]
        #   condition: True
        return {
            "scheduled_time": {
                "permission_roles": [EMeetingUserRole.organizer, EMeetingUserRole.attendee],
                "condition": lambda old_time, new_time: new_time >= old_time
            }
        }


# For user status in a meeting
class MeetingResponse(BaseModel):
    user_id: int
    role: EMeetingUserRole
    response: EMeetingResponseStatus | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingRequestRead(BaseModel):
    id: int
    match_id: int | None = None
    description: str | None = None
    location: EMeetingLocation
    scheduled_time: datetime
    status: EMeetingStatus
    user_responses: list[MeetingResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingFilter(BaseModel):
    user_id: int | None = None
    user_role: EMeetingUserRole | list[EMeetingUserRole] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    meeting_status: EMeetingStatus | list[EMeetingStatus] | None = None
    user_response: EMeetingResponseStatus | list[EMeetingResponseStatus] | None = None
    location: EMeetingLocation | list[EMeetingLocation] | None = None


class MeetingList(BaseModel):
    meetings: list[MeetingRequestRead]


class MeetingsUserLimits(BaseModel):
    meetings_pendings_limit: int = 0
    meetings_confirmations_limit: int = 0
    available_meeting_pendings: int = 0
    available_meeting_confirmations: int = 0
