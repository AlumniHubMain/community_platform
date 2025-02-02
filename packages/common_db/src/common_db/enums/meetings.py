from enum import Enum
from sqlalchemy import Enum as PGEnum


class EMeetingStatus(Enum):
    no_answer = 'no_answer'
    archived = 'archived'
    confirmed = 'confirmed'


class EMeetingResponseStatus(Enum):
    no_answer = 'no_answer'
    confirmed = 'confirmed'
    declined = 'declined'


class EMeetingUserRole(Enum):
    organizer = 'organizer'
    attendee = 'attendee'


class EMeetingLocation(Enum):
    anywhere = 'anywhere'
    offline = 'offline'
    online = 'online'


MeetingStatusPGEnum = PGEnum(
    EMeetingStatus,
    name="meeting_status_enum",
    inherit_schema=True,
)

MeetingUserRolePGEnum = PGEnum(
    EMeetingUserRole,
    name="meeting_user_role_enum",
    inherit_schema=True,
)

MeetingResponseStatusPGEnum = PGEnum(
    EMeetingResponseStatus,
    name="meeting_response_status_enum",
    inherit_schema=True,
)

MeetingLocationPGEnum = PGEnum(
    EMeetingLocation,
    name="meeting_location_enum",
    inherit_schema=True,
)