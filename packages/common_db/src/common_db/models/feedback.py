
from sqlalchemy import Index, PrimaryKeyConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from common_db.config import schema
from common_db.models.base import ObjectTable


class ORMMeetingFeedback(ObjectTable):
    """
    Meeting feedbacks table.
    """

    __tablename__ = 'meeting_feedbacks'
    __table_args__ = (
        Index('ix_meeting_feedback_meeting_id', 'meeting_id'),
        Index('ix_meeting_feedback_user_id', 'user_id'),
        PrimaryKeyConstraint('meeting_id', 'id'),
        PrimaryKeyConstraint('user_id', 'id'),
        {'schema': schema},
    )
    
    meeting_id: Mapped[int] = mapped_column(Integer, 
                                            ForeignKey(f'{schema}.meetings.id', ondelete="CASCADE"),
                                            primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, 
                                         ForeignKey(f'{schema}.users.id', ondelete="CASCADE"),
                                         primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
