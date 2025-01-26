from enum import Enum
from sqlalchemy import Enum as PGEnum

class EIntentType(Enum):
    """
    Types of thematical blocks for users matching.
    """
    connect = "connect"
    mentoring = "mentoring"
    mock_interview = "mock_interview"
    help_request = "help_request"
    referal = "referal"


class EMeetingFormat(Enum):
    """
    Types of selected meeting format.
    """
    offline = "offline"
    online = "online"
    both = "any"

# PostgreSQL Enum types
MeetingIntentMeetingTypePGEnum = PGEnum(
    EIntentType,
    name="meeting_intent_meeting_type",
    inherit_schema=True,
)

MeetingFormatPGEnum = PGEnum(
    EMeetingFormat,
    name="meeting_format",
    inherit_schema=True,
)
