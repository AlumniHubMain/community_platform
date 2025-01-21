from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from common_db.meetings import EMeetingUserRole, EMeetingResponseStatus, EMeetingStatus


# For creating meeting requests
class MeetingRequestCreate(BaseModel):
    organizer_id: int
    match_id: int
    attendees_id: list[int]
    scheduled_time: datetime | None = None
    location: str # TODO: @ilyabiro change to enum 
    description: str | None = None


# For reading meeting info
class MeetingRequestRead(BaseModel):
    id: int
    match_id: int
    description: str | None = None
    location: str # TODO: @ilyabiro change to enum
    scheduled_time: datetime
    status: EMeetingStatus
    user_responses: list[MeetingResponse]  # List of users with their statuses

    class Config:
        from_attributes = True


class MeetingRequestUpdate(BaseModel):
    description: str | None = None
    location: str | None = None
    scheduled_time: datetime | None = None
    
    @staticmethod
    def get_update_rules():
        # Default:
        #   permission: [organizer]
        #   condition: True
        return {
            "scheduled_time": {
                "permission_roles": [EMeetingUserRole.organizer, EMeetingUserRole.attendee],
                "condition": "{old_value} > {new_value}"
            }
        }


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
