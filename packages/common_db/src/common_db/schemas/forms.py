from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from common_db.enums.forms import EFormMeetingType, EFormQueryType, EFormHelpRequestType, EFormLookingForType


class Form(BaseModel):
    user_id: int
    meeting_type: EFormMeetingType
    query_type: EFormQueryType
    help_request_type: EFormHelpRequestType
    looking_for_type: EFormLookingForType
    calendar: str
    description: str | None = None


class SFormRead(Form):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
