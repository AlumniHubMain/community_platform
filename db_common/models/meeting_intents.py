from sqlalchemy import String, BIGINT, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from db_common.enums.meeting_intents import (
    EMeetingIntentQueryType, EMeetingIntentHelpRequestType,
    EMeetingIntentLookingForType, EMeetingIntentMeetingType,
    MeetingIntentQueryTypePGEnum, MeetingIntentHelpRequestTypePGEnum,
    MeetingIntentLookingForTypePGEnum, MeetingIntentMeetingTypePGEnum,
)
from .base import ObjectTable

class ORMMeetingIntent(ObjectTable):
    """
    Модель таблицы (шаблон) LinkedIn profiles.
    """

    __tablename__ = "meeting_intents"

    user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("users.id"))

    meeting_type: Mapped[EMeetingIntentMeetingType] = mapped_column(MeetingIntentMeetingTypePGEnum)

    query_type: Mapped[EMeetingIntentQueryType] = mapped_column(MeetingIntentQueryTypePGEnum)

    help_request_type: Mapped[EMeetingIntentHelpRequestType] = mapped_column(MeetingIntentHelpRequestTypePGEnum)

    looking_for_type: Mapped[EMeetingIntentLookingForType] = mapped_column(MeetingIntentLookingForTypePGEnum)

    text_intent: Mapped[str | None] = mapped_column(String(500))

