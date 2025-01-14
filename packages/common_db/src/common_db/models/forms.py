
from sqlalchemy import Index, PrimaryKeyConstraint, ForeignKey, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column
from common_db.config import schema
from common_db.models.base import ObjectTable
from common_db.enums.forms import EIntentType, EMeetingFormat, MeetingIntentMeetingTypePGEnum, MeetingFormatPGEnum

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
    intent_type: Mapped[EIntentType] = mapped_column(MeetingIntentMeetingTypePGEnum, nullable=False)
    meeting_format: Mapped[EMeetingFormat] = mapped_column(MeetingFormatPGEnum, nullable=False)
    # TODO: Change to calendar format. Maybe String(200) - very small size for this.
    calendar: Mapped[str] = mapped_column(String(200))
    available_meetings_count: Mapped[int] = mapped_column(Integer)
