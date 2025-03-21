from datetime import datetime
from sqlalchemy import DateTime, Integer, ForeignKey, Index, PrimaryKeyConstraint, Text, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common_db.enums.meetings import (
    EMeetingStatus,
    MeetingStatusPGEnum,
    EMeetingUserRole,
    MeetingUserRolePGEnum,
    EMeetingResponseStatus,
    MeetingResponseStatusPGEnum,
    EMeetingLocation,
    MeetingLocationPGEnum,
)
from common_db.config import schema
from common_db.models.base import ObjectTable


class ORMMeeting(ObjectTable):
    """
    Meetings table.
    """

    __tablename__ = 'meetings'
    __table_args__ = (
        Index('ix_meeting_id', 'id'),
        Index('ix_meeting_status', 'status'),
        Index('ix_meeting_time', 'scheduled_time'),
        PrimaryKeyConstraint('id', 'organizer_id', 'match_id'),
        {'schema': schema},
    )

    # Define composite primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organizer_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey(f'{schema}.users.id', ondelete="CASCADE"),
        primary_key=True
    )
    match_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey(f'{schema}.matching_results.id', ondelete="CASCADE"),
        primary_key=True,
        nullable=True
    )

    # Meeting-specific fields
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location: Mapped[EMeetingLocation] = mapped_column(MeetingLocationPGEnum, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[EMeetingStatus] = mapped_column(
        MeetingStatusPGEnum, 
        nullable=False, 
        default=EMeetingStatus.no_answer
    )

    # Relationship to user_meetings table via ORMUserMeeting
    user_responses: Mapped[list["ORMMeetingResponse"]] = relationship(
        "ORMMeetingResponse", 
        back_populates="meeting", 
        cascade="all, delete-orphan"
    )


class ORMMeetingResponse(ObjectTable):
    """
    Meeting responses table.
    """
    __tablename__ = 'meeting_responses'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'meeting_id', 'meeting_organizer_id', 'meeting_match_id'),
        ForeignKeyConstraint(
            ['meeting_id', 'meeting_organizer_id', 'meeting_match_id'],
            [f'{schema}.meetings.id', f'{schema}.meetings.organizer_id', f'{schema}.meetings.match_id'],
            ondelete="CASCADE",
            name='fk_meeting_response_meeting'
        ),
        {'schema': schema}
    )

    # Remove id from base class since we're defining composite primary key
    id = None

    # Foreign keys as composite primary key
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey(f'{schema}.users.id', ondelete="CASCADE"),
        primary_key=True
    )
    meeting_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    meeting_organizer_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    meeting_match_id: Mapped[int | None] = mapped_column(
        Integer,
        primary_key=True,
        nullable=True
    )

    role: Mapped[EMeetingUserRole] = mapped_column(MeetingUserRolePGEnum, nullable=False)
    response: Mapped[EMeetingResponseStatus] = mapped_column(
        MeetingResponseStatusPGEnum, 
        nullable=False,
        default=EMeetingResponseStatus.no_answer
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["ORMUserProfile"] = relationship("ORMUserProfile", back_populates="meeting_responses")
    meeting: Mapped["ORMMeeting"] = relationship("ORMMeeting", back_populates="user_responses")
