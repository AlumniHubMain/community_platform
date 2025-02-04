from datetime import datetime
from pydantic import BaseModel

from common_db.schemas.base import BaseSchema, TimestampedSchema
from common_db.enums.forms import (
    EFormQueryType,
    EFormHelpRequestType,
    EFormMeetingType,
    EFormLookingForType,
)


class FormBase(BaseSchema):
    """Base schema for forms"""
    user_id: int
    meeting_type: EFormMeetingType
    query_type: EFormQueryType
    help_request_type: EFormHelpRequestType
    looking_for_type: EFormLookingForType
    calendar: str
    description: str | None = None


class FormCreate(FormBase):
    """Schema for creating a form"""
    pass


class FormUpdate(BaseModel):
    """Schema for updating a form"""
    meeting_type: EFormMeetingType | None = None
    query_type: EFormQueryType | None = None
    help_request_type: EFormHelpRequestType | None = None
    looking_for_type: EFormLookingForType | None = None
    calendar: str | None = None
    description: str | None = None


class FormRead(FormBase, TimestampedSchema):
    """Schema for reading a form"""
    pass


# For filtering/listing forms
class FormFilter(BaseModel):
    """Schema for filtering forms"""
    user_id: int | None = None
    meeting_type: EFormMeetingType | list[EFormMeetingType] | None = None
    query_type: EFormQueryType | list[EFormQueryType] | None = None
    help_request_type: EFormHelpRequestType | list[EFormHelpRequestType] | None = None
    looking_for_type: EFormLookingForType | list[EFormLookingForType] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class FormList(BaseModel):
    """Schema for list of forms"""
    forms: list[FormRead] 