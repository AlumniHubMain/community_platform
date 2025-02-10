from common_db.schemas.base import BaseSchema, TimestampedSchema
from typing import Annotated
from common_db.schemas.validators import IntegerRangeValidator


FEEDBACK_MINIMAL_RATE = 1
FEEDBACK_MAXIMUM_RATE = 5
FEEDBACK_RATE_VALIDATOR = IntegerRangeValidator(min=FEEDBACK_MINIMAL_RATE, max=FEEDBACK_MAXIMUM_RATE)


class MeetingFeedbackBase(BaseSchema):
    user_id: int
    meeting_id: int
    rate: Annotated[int, FEEDBACK_RATE_VALIDATOR]
    text: str


class MeetingFeedbackCreate(MeetingFeedbackBase):
    """Schema for creating a meeting feedback"""
    pass


class MeetingFeedbackRead(MeetingFeedbackBase, TimestampedSchema):
    """Schema for reading a meeting feedback"""
    pass
