from enum import Enum
from sqlalchemy import Enum as PGEnum


class EMeetingStatus(Enum):
    new = 'new'
    archived = 'archived'
    confirmed = 'confirmed'


class EMeetingResponseStatus(Enum):
    no_answer = 'no_answer'
    confirmed = 'confirmed' 
    tentative = 'tentative' 
    declined = 'declined'
    
    def is_confirmed_status(self) -> bool:
        # Check if meeting confirmed
        return EMeetingResponseStatus(self.value) in (EMeetingResponseStatus.confirmed, EMeetingResponseStatus.tentative)

    def is_pended_status(self) -> bool:
        # Check if meeting pended
        return EMeetingResponseStatus(self.value) != EMeetingResponseStatus.declined


class EMeetingUserRole(Enum):
    organizer = 'organizer'
    attendee = 'attendee'

MeetingStatusPGEnum = PGEnum(
    EMeetingStatus,
    name="meeting_status",
    inherit_schema=True,
)

MeetingUserRolePGEnum = PGEnum(
    EMeetingUserRole,
    name="meeting_user_role",
    inherit_schema=True,
)

MeetingResponseStatusPGEnum = PGEnum(
    EMeetingResponseStatus,
    name="meeting_response_status",
    inherit_schema=True,
)
