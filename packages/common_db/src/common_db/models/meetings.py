from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Index, PrimaryKeyConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common_db.enums.meetings import (
    EMeetingStatus,
    MeetingStatusPGEnum,
    EMeetingUserRole,
    MeetingUserRolePGEnum,
    EMeetingResponseStatus,
    MeetingResponseStatusPGEnum,
)
from common_db.config import schema
from common_db.models.base import ObjectTable


class ORMMeeting(ObjectTable):
    """
    Meetings table.
    """

    __tablename__ = 'meetings'
    __table_args__ = (
        Index('ix_meeting_status', 'status'),
        Index('ix_meeting_time', 'scheduled_time'),
        {'schema': schema},
    )

    # Meeting-specific fields
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[EMeetingStatus] = mapped_column(MeetingStatusPGEnum, nullable=False, default=EMeetingStatus.new)

    # Relationship to user_meetings table via ORMUserMeeting
    user_responses: Mapped[list["ORMMeetingResponse"]] = relationship(
        "ORMMeetingResponse", back_populates="meeting", cascade="all, delete-orphan"
    )


class ORMMeetingResponse(ObjectTable):
    """
    User's responses to meetings.
    """

    __tablename__ = 'meeting_responses'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'meeting_id'),
        {'schema': schema},
    )
    id = None  # no separate ids

    # Two foreign keys, one for users and one for meetings
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(f'{schema}.users.id', ondelete="CASCADE"),
                                         primary_key=True)
    meeting_id: Mapped[int] = mapped_column(Integer, ForeignKey(f'{schema}.meetings.id', ondelete="CASCADE"),
                                            primary_key=True)

    role: Mapped[EMeetingUserRole] = mapped_column(MeetingUserRolePGEnum, nullable=False)
    response: Mapped[EMeetingResponseStatus] = mapped_column(MeetingResponseStatusPGEnum, nullable=False)

    # Relationships for back-population
    user: Mapped["ORMUserProfile"] = relationship("ORMUserProfile", back_populates="meeting_responses")
    meeting: Mapped["ORMMeeting"] = relationship("ORMMeeting", back_populates="user_responses")
