
from sqlalchemy import Index, PrimaryKeyConstraint, ForeignKey, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column
from common_db.config import schema
from common_db.models.base import ObjectTable
from common_db.enums.forms import (
    EFormMeetingType,
    FormMeetingTypePGEnum,
    EFormLookingForType,
    FormLookingForTypePGEnum,
    EFormHelpRequestType,
    FormHelpRequestTypePGEnum,
    EFormQueryType,
    FormQueryTypePGEnum,
)
    

class ORMForm(ObjectTable):
    """
    Forms table.
    """

    __tablename__ = 'forms'
    __table_args__ = (
        Index('ix_form_query_type', 'query_type'),
        PrimaryKeyConstraint('user_id', 'id'),
        {'schema': schema},
    )
    
    user_id: Mapped[int] = mapped_column(Integer, 
                                         ForeignKey(f'{schema}.users.id', ondelete="CASCADE"),
                                         primary_key=True)
    meeting_type: Mapped[EFormMeetingType] = mapped_column(FormMeetingTypePGEnum, nullable=False)
    query_type: Mapped[EFormQueryType] = mapped_column(FormQueryTypePGEnum, nullable=False)
    help_request_type: Mapped[EFormHelpRequestType] = mapped_column(FormHelpRequestTypePGEnum, nullable=False)
    looking_for_type: Mapped[EFormLookingForType] = mapped_column(FormLookingForTypePGEnum, nullable=False)
    calendar: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
