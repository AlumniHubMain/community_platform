from datetime import datetime
from enum import Enum

from sqlalchemy import String, Index, Integer, Text, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import mapped_column, Mapped, relationship

from .db_abstract import ObjectTable, schema


class EMeetingsStatus(Enum):
    new = 'new'
    archived = 'archived'
    confirmed = 'confirmed'


class EMeetingResponseStatus(Enum):
    confirmed = 'confirmed' 
    tentative = 'tentative' 
    declined = 'declined'


class EMeetingUserRole(Enum):
    organizer = 'organizer'
    attendee = 'attendee'


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
    status: Mapped[str] = mapped_column(ENUM(EMeetingsStatus, name='meeting_status'), 
                                        nullable=False,
                                        default=EMeetingsStatus.new)

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

    role: Mapped[str] = mapped_column(ENUM(EMeetingUserRole, name='meeting_user_role'), nullable=False)
    response: Mapped[str | None] = mapped_column(ENUM(EMeetingResponseStatus, name='meeting_response'))

    # Relationships for back-population
    user: Mapped["ORMUserProfile"] = relationship("ORMUserProfile", back_populates="meeting_responses")
    meeting: Mapped["ORMMeeting"] = relationship("ORMMeeting", back_populates="user_responses")
