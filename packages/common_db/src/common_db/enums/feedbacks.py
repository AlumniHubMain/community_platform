from enum import Enum
from sqlalchemy import Enum as PGEnum


class EMeetingFeedbackBenefit(Enum):
    useful = "useful"
    pointless = "pointless"
    partial = "partial"


MeetingFeedbackBenefitPGEnum = PGEnum(
    EMeetingFeedbackBenefit,
    name="meeting_feedback_benefit_enum",
    inherit_schema=True,
)
