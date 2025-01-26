from __future__ import annotations
from pydantic import BaseModel
from common_db.enums.forms import EIntentType, EMeetingFormat


class Form(BaseModel):
    form: str
    description: str | None    
    intent_type: EIntentType
    meeting_format: EMeetingFormat
    calendar: str
    available_meetings_count: int
    user_id: int


class SFormRead(Form):
    id: int
    
    class Config:
        from_attributes = True
