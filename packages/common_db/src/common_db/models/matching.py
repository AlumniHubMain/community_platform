from sqlalchemy import String, Integer, JSON, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from .base import ObjectTable, schema


class ORMMatchingResult(ObjectTable):
    """
    Model for storing matching results
    """

    __tablename__ = "matching_results"
    __table_args__ = {"schema": schema}

    model_settings_preset: Mapped[str] = mapped_column(String(50), nullable=False)
    match_users_count: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{schema}.users.id"), nullable=False)
    form_id: Mapped[int] = mapped_column(Integer, nullable=True)  # Optional form ID
    intent_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{schema}.meeting_intents.id"), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_details: Mapped[dict | None] = mapped_column(JSON)
    matching_result: Mapped[list[int]] = mapped_column(ARRAY(Integer))
