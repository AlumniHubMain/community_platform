
from sqlalchemy import Index, ForeignKeyConstraint, ForeignKey, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from common_db.config import schema
from common_db.models.base import ObjectTable
from common_db.enums.feedbacks import EMeetingFeedbackBenefit, MeetingFeedbackBenefitPGEnum


class ORMMeetingFeedback(ObjectTable):
    """
    Meeting feedbacks table.
    """

    __tablename__ = 'meeting_feedbacks'
    __table_args__ = (
        Index('ix_meeting_feedback_meeting_id', 'meeting_id'),
        Index('ix_meeting_feedback_from_user_id', 'to_user_id'),
        Index('ix_meeting_feedback_to_user_id', 'from_user_id'),
        ForeignKeyConstraint(
            ['meeting_id'],
            [f'{schema}.meetings.id'],
            ondelete="CASCADE",
            name='fk_meeting_feedbacks_meetings'
        ),
        {'schema': schema},
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(Integer, 
                                            ForeignKey(f'{schema}.meetings.id', ondelete="CASCADE"),
                                            primary_key=True)
    from_user_id: Mapped[int] = mapped_column(Integer, 
                                              ForeignKey(f'{schema}.users.id', ondelete="CASCADE"),
                                              primary_key=True)
    to_user_id: Mapped[int] = mapped_column(Integer, 
                                            ForeignKey(f'{schema}.users.id', ondelete="CASCADE"),
                                            primary_key=True)
    rate: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
    goal_matching_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    assignee_preparation_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    meeting_benefits: Mapped[EMeetingFeedbackBenefit] = mapped_column(MeetingFeedbackBenefitPGEnum, nullable=False)
