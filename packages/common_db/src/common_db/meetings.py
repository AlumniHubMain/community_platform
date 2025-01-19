from datetime import datetime
from enum import Enum

from sqlalchemy import ARRAY, String, Index, Integer, Text, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import mapped_column, Mapped, relationship

from .db_abstract import ObjectTable, schema


class EMeetingStatus(Enum):
    no_answer = 'no_answer'
    archived = 'archived'
    confirmed = 'confirmed'


class EMeetingResponseStatus(Enum):
    no_answer = 'no_answer'
    confirmed = 'confirmed' 
    declined = 'declined'
    
    def is_confirmed_status(self) -> bool:
        # Check if meeting confirmed
        return EMeetingResponseStatus(self.value) in EMeetingResponseStatus.confirmed

    def is_pended_status(self) -> bool:
        # Check if meeting pended
        return EMeetingResponseStatus(self.value) != EMeetingResponseStatus.declined


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
    organizer_id: Mapped[int] = mapped_column(Integer, ForeignKey(f'{schema}.users.id', ondelete="CASCADE"), 
                                              primary_key=True)
    match_id: Mapped[int] = mapped_column(Integer) # TODO: Change to ForeignKey(f'{schema}.matches.id', ondelete="CASCADE"), primary_key=True
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(ENUM(EMeetingStatus, name='meeting_status_enum'), 
                                        nullable=False,
                                        default=EMeetingStatus.no_answer)

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

    role: Mapped[str] = mapped_column(ENUM(EMeetingUserRole, name='meeting_user_role_enum'), nullable=False)
    response: Mapped[str] = mapped_column(ENUM(EMeetingResponseStatus, name='meeting_response_enum'), nullable=False)

    # Relationships for back-population
    user: Mapped["ORMUserProfile"] = relationship("ORMUserProfile", back_populates="meeting_responses")
    meeting: Mapped["ORMMeeting"] = relationship("ORMMeeting", back_populates="user_responses")
