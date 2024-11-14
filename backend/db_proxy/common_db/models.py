from datetime import datetime
from typing import List

from sqlalchemy import ARRAY, String, BIGINT, Index, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import mapped_column, Mapped, relationship, declared_attr

from .db_abstract import ObjectTable, schema


class ORMUserProfile(ObjectTable):
    """
    Модель таблицы (шаблон) пользователей.
    """

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)

    avatars: Mapped[List[str] | None] = mapped_column(ARRAY(String(300)))

    city_live: Mapped[str | None] = mapped_column(String(200))
    country_live: Mapped[str | None] = mapped_column(String(100))
    phone_number: Mapped[str | None] = mapped_column(String(20))
    linkedin_link: Mapped[str | None] = mapped_column(String(100))

    telegram_name: Mapped[str | None] = mapped_column(String(200))
    telegram_id: Mapped[int | None] = mapped_column(BIGINT)
    is_tg_bot_blocked: Mapped[bool] = mapped_column(default=False)
    blocked_status_update_date: Mapped[datetime | None]

    requests_to_society: Mapped[List[str] | None] = mapped_column(ARRAY(String(100)))
    professional_interests: Mapped[List[str] | None] = mapped_column(ARRAY(String(100)))

    __table_args__ = (Index('ix_users_telegram_id', 'telegram_id'),
                      {'schema': f"{schema}"}
                      )


class ORMMeeting(ObjectTable):
    """
    Модель таблицы встреч.
    """

    __tablename__ = 'meetings'

    # Meeting-specific fields
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(ENUM('new', 'confirmed', 'archived', name='meeting_status'), nullable=False, default="new")

    # Relationship to user_meetings table
    users: Mapped[List[ORMUserProfile]] = relationship(
        "ORMUserProfile", secondary="user_meetings", back_populates="meetings"
    )

    @declared_attr
    def __table_args__(cls):
        # Optionally, you could add any indexes or additional constraints here.
        return (
            Index('ix_meeting_status', 'status'),
        )


class ORMUserMeeting(ObjectTable):
    """
    Модель для связи пользователей с встречами.
    """

    __tablename__ = 'user_meetings'

    uid: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    meeting_id: Mapped[int] = mapped_column(Integer, ForeignKey('meetings.id', ondelete="CASCADE"), primary_key=True)

    role: Mapped[str] = mapped_column(ENUM('organizer', 'attendee', name='user_role'), nullable=False)
    agreement: Mapped[str | None] = mapped_column(ENUM('confirmed', 'tentative', 'declined', name='agreement'))

    # Relationships for back-population
    user: Mapped[ORMUserProfile] = relationship("ORMUserProfile", back_populates="user_meetings")
    meeting: Mapped[ORMMeeting] = relationship("ORMMeeting", back_populates="users")
