from enum import Enum
from sqlalchemy import Enum as PGEnum


class EMeetingStatus(Enum):
    new = 'new'
    confirmed = 'confirmed'
    archived = 'archived'

class EMeetingUserRole(Enum):
    organizer = 'organizer'
    attendee = 'attendee'

class EMeetingResponse(Enum):
    confirmed = 'confirmed'
    tentative = 'tentative'
    declined = 'declined'

MeetingStatusPGEnum = PGEnum(EMeetingStatus, name='meeting_status', inherit_schema=True)
MeetingUserRolePGEnum = PGEnum(EMeetingUserRole, name='meeting_user_role', inherit_schema=True)
MeetingResponsePGEnum = PGEnum(EMeetingResponse, name='meeting_response', inherit_schema=True)
