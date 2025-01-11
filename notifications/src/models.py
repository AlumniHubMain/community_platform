from datetime import datetime

from sqlalchemy import String, BIGINT, ARRAY, Index
from sqlalchemy.orm import mapped_column, Mapped

from common_db.db_abstract import ObjectTable, schema


class ORMUserProfile(ObjectTable):
    """
    Модель таблицы (шаблон) пользователей.
    """

    __tablename__ = 'users'

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
    requests_to_society: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    professional_interests: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    timezone: Mapped[str | None]
    is_tg_notify: Mapped[bool] = mapped_column(default=False)
    is_email_notify: Mapped[bool] = mapped_column(default=False)
    is_push_notify: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (Index('ix_users_telegram_id', 'telegram_id'),
                      {'schema': f"{schema}",
                       'extend_existing': True}
                      )
