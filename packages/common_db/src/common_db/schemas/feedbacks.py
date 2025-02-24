from common_db.schemas.base import BaseSchema, TimestampedSchema
from common_db.enums.feedbacks import EMeetingFeedbackBenefit
from pydantic import model_validator


FEEDBACK_MINIMAL_RATE = 1
FEEDBACK_MAXIMUM_RATE = 5


class MeetingFeedbackBase(BaseSchema):
    to_user_id: int
    meeting_id: int
    rate: int
    text: str | None = None
    goal_matching_rate: int
    assignee_preparation_rate: int
    meeting_benefits: EMeetingFeedbackBenefit
    is_want_another_meeting: bool
    is_recommendation: bool
    
    @model_validator(mode='after')
    def extended_model_validation(self):
        
        if self.rate < FEEDBACK_MINIMAL_RATE or self.rate > FEEDBACK_MAXIMUM_RATE:
            raise ValueError(f"\"rate\" must be in range [{FEEDBACK_MINIMAL_RATE}, {FEEDBACK_MAXIMUM_RATE}]. Got: {self.rate}")
        
        if self.goal_matching_rate < FEEDBACK_MINIMAL_RATE or self.goal_matching_rate > FEEDBACK_MAXIMUM_RATE:
            raise ValueError(f"\"goal_matching_rate\" must be in range [{FEEDBACK_MINIMAL_RATE}, {FEEDBACK_MAXIMUM_RATE}]. Got: {self.goal_matching_rate}")
        
        if self.assignee_preparation_rate < FEEDBACK_MINIMAL_RATE or self.assignee_preparation_rate > FEEDBACK_MAXIMUM_RATE:
            raise ValueError(f"\"assignee_preparation_rate\" must be in range [{FEEDBACK_MINIMAL_RATE}, {FEEDBACK_MAXIMUM_RATE}]. Got: {self.assignee_preparation_rate}")
        
        return self


class MeetingFeedbackCreate(MeetingFeedbackBase):
    """Schema for creating a meeting feedback"""
    pass


class MeetingFeedbackRead(MeetingFeedbackBase, TimestampedSchema):
    """Schema for reading a meeting feedback"""
    from_user_id: int
