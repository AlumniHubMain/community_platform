from sqlalchemy import Index, PrimaryKeyConstraint, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from common_db.config import schema
from common_db.models.base import ObjectTable
from common_db.enums.forms import (
    EFormIntentType,
    FormIntentTypePGEnum,
)


class ORMForm(ObjectTable):
    """
    Forms table.
    """

    __tablename__ = 'forms'
    __table_args__ = (
        Index('ix_form_intent', 'intent'),
        PrimaryKeyConstraint('user_id', 'id'),
        {'schema': schema},
    )
    
    user_id: Mapped[int] = mapped_column(Integer, 
                                         ForeignKey(f'{schema}.users.id', ondelete="CASCADE"),
                                         primary_key=True)
    intent: Mapped[EFormIntentType] = mapped_column(FormIntentTypePGEnum, nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    calendar: Mapped[str] = mapped_column(String(200), nullable=False)
