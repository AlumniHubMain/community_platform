from __future__ import annotations

from .db_abstract import ObjectTable

from sqlalchemy import ARRAY, String, BIGINT
from sqlalchemy.orm import mapped_column, Mapped

from typing import List


class ORMUserProfile(ObjectTable):
    """
    Модель таблицы (шаблон) пользователей.
    """

    #ToDo(evseev.dmsr): научить 3.9 работать с типами X | Y, или поднять версию до 3.10
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)

    avatars: Mapped[List[str]] = mapped_column(ARRAY(String(300)))

    city_live: Mapped[str] = mapped_column(String(200))
    country_live: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[str] = mapped_column(String(20))
    linkedin_link: Mapped[str] = mapped_column(String(100))

    telegram_name: Mapped[str] = mapped_column(String(200))
    telegram_id: Mapped[int] = mapped_column(BIGINT)

    requests_to_society: Mapped[List[str]] = mapped_column(ARRAY(String(100)))
    professional_interests: Mapped[List[str]] = mapped_column(ARRAY(String(100)))
