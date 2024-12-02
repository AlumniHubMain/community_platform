from sqlalchemy import String, Index, Integer, Text, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import mapped_column, Mapped
from forms.schemas import EIntentType, EMeetingFormat
from .db_abstract import ObjectTable, schema
from enum import Enum


class EIntentType(str, Enum):
    """
    Types of thematical blocks for users matching.
    """
    connect = "connect"
    mentoring = "mentoring"
    mock_interview = "mock_interview"
    help_request = "help_request"
    referal = "referal"


class EMeetingFormat(str, Enum):
    """
    Types of selected meeting format.
    """
    offline = "offline"
    online = "online"
    both = "any"


class ORMForm(ObjectTable):
    """
    Forms table.
    """

    __tablename__ = 'forms'
    __table_args__ = (
        Index('ix_form_intent_type', 'intent_type'),
        PrimaryKeyConstraint('user_id', 'id'),
        {'schema': schema},
    )
    
    user_id: Mapped[int] = mapped_column(Integer, 
                                         ForeignKey(f'{schema}.users.id', ondelete="CASCADE"),
                                         primary_key=True)
    form: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    intent_type: Mapped[EIntentType] = mapped_column(ENUM(EIntentType, 
                                                          name='e_intent_type', 
                                                          create_constraint=False), 
                                                     nullable=False)
    meeting_format: Mapped[EMeetingFormat] = mapped_column(ENUM(EMeetingFormat, 
                                                                name='e_meeting_format', 
                                                                create_constraint=False), 
                                                           nullable=False)
    # TODO: Change to calendar format. Maybe String(200) - very small size for this.
    calendar: Mapped[str] = mapped_column(String(200))
    available_meetings_count: Mapped[int] = mapped_column(Integer)
