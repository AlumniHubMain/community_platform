from datetime import datetime
from common_db.enums.meetings import EMeetingStatus, EMeetingUserRole, EMeetingResponseStatus, EMeetingLocation
from common_db.schemas.base import BaseSchema, TimestampedSchema

from pydantic import model_validator


class MeetingResponseRead(TimestampedSchema):
    user_id: int
    meeting_id: int
    role: EMeetingUserRole
    response: EMeetingResponseStatus | None = None
    description: str | None = None


class MeetingRead(TimestampedSchema):
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime
    status: EMeetingStatus
    user_responses: list[MeetingResponseRead]


class MeetingRequestCreate(BaseSchema):
    match_id: int | None = None
    attendees_id: list[int]
    scheduled_time: datetime | None = None
    location: EMeetingLocation
    description: str | None = None


class MeetingRequestUpdateUserResponse(BaseSchema):
    status: EMeetingResponseStatus
    description: str | None = None
    
    @model_validator(mode='after')
    def validate_depended_fields(self):
        if self.status == EMeetingResponseStatus.declined:
            if self.description is None:
                raise ValueError("\"description\" field must be filled when setted the \"declined\" meeting response")
        return self


class MeetingRequestUpdate(BaseSchema):
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
class MeetingResponse(TimestampedSchema):
    user_id: int
    role: EMeetingUserRole
    response: EMeetingResponseStatus | None = None
    description: str | None = None


class MeetingRequestRead(TimestampedSchema):
    match_id: int | None = None
    description: str | None = None
    location: EMeetingLocation
    scheduled_time: datetime
    status: EMeetingStatus
    user_responses: list[MeetingResponse]


class MeetingFilter(BaseSchema):
    user_role: EMeetingUserRole | list[EMeetingUserRole] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    meeting_status: EMeetingStatus | list[EMeetingStatus] | None = None
    user_response: EMeetingResponseStatus | list[EMeetingResponseStatus] | None = None
    location: EMeetingLocation | list[EMeetingLocation] | None = None


class MeetingList(BaseSchema):
    meetings: list[MeetingRequestRead]


class MeetingsUserLimits(BaseSchema):
    meetings_pendings_limit: int = 0
    meetings_confirmations_limit: int = 0
    available_meeting_pendings: int = 0
    available_meeting_confirmations: int = 0
