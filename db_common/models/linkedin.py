from sqlalchemy import String, JSON, ForeignKey, ARRAY, BIGINT
from sqlalchemy.orm import Mapped, mapped_column
from .base import ObjectTable, schema


class ORMLinkedInProfile(ObjectTable):
    """
    Модель таблицы (шаблон) LinkedIn profiles.
    """

    __tablename__ = "linkedin_profiles"
    __table_args__ = {"schema": schema}

    user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey(f"{schema}.users.id"), primary_key=True)

    profile_url: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String(100))

    headline: Mapped[str | None] = mapped_column(String(100))
    location_name: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    summary: Mapped[str | None] = mapped_column(String(1000))

    experience: Mapped[list[dict] | None] = mapped_column(ARRAY(JSON))
    education: Mapped[list[dict] | None] = mapped_column(ARRAY(JSON))
    languages: Mapped[list[dict] | None] = mapped_column(ARRAY(JSON))
    skills: Mapped[dict | None] = mapped_column(JSON)
    connections: Mapped[dict | None] = mapped_column(JSON)
