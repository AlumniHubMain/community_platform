from pydantic import BaseModel
from db_common.enums.meeting_intents import (
    EMeetingIntentMeetingType,
    EMeetingIntentQueryType,
    EMeetingIntentHelpRequestType,
    EMeetingIntentLookingForType,
)


class MeetingIntent(BaseModel):
    """
    Модель таблицы (шаблон) Meeting intents.
    """
    user_id: int
    meeting_type: EMeetingIntentMeetingType

    query_type: EMeetingIntentQueryType

    help_request_type: EMeetingIntentHelpRequestType

    looking_for_type: EMeetingIntentLookingForType

    text_intent: str | None



class SMeetingIntentRead(MeetingIntent):
    id: int

    class Config:
        from_attributes = True
