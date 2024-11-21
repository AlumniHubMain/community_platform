from datetime import datetime

from sqlalchemy import ARRAY, String, BIGINT, Index, Integer, Text, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import mapped_column, Mapped, relationship

from .db_abstract import ObjectTable, schema, Base


class ORMUserProfile(ObjectTable):
    """
    Модель таблицы (шаблон) пользователей.
    """

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)

    avatars: Mapped[list[str] | None] = mapped_column(ARRAY(String(300)))

    city_live: Mapped[str | None] = mapped_column(String(200))
    country_live: Mapped[str | None] = mapped_column(String(100))
    phone_number: Mapped[str | None] = mapped_column(String(20))
    linkedin_link: Mapped[str | None] = mapped_column(String(100))

    telegram_name: Mapped[str | None] = mapped_column(String(200))
    telegram_id: Mapped[int | None] = mapped_column(BIGINT)
    is_tg_bot_blocked: Mapped[bool] = mapped_column(default=False)
    blocked_status_update_date: Mapped[datetime | None]

    requests_to_society: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)))
    professional_interests: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)))

    # Relationship for user_meetings, linking the user to their meetings with roles and responses
    meeting_responses: Mapped[list["ORMMeetingResponse"]] = relationship(
        "ORMMeetingResponse", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (Index('ix_users_telegram_id', 'telegram_id'),
                      {'schema': f"{schema}"}
                      )


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
    status: Mapped[str] = mapped_column(ENUM('new', 'confirmed', 'archived', name='meeting_status'), nullable=False,
                                        default="new")

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

    role: Mapped[str] = mapped_column(ENUM('organizer', 'attendee', name='meeting_user_role'), nullable=False)
    response: Mapped[str | None] = mapped_column(ENUM('confirmed', 'tentative', 'declined', name='meeting_response'))

    # Relationships for back-population
    user: Mapped["ORMUserProfile"] = relationship("ORMUserProfile", back_populates="meeting_responses")
    meeting: Mapped["ORMMeeting"] = relationship("ORMMeeting", back_populates="user_responses")
