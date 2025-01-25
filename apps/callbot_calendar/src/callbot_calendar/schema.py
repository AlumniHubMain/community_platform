from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


class Event(BaseModel):
    google_id: str  # The unique ID of the event from Google Calendar
    subject: str  # The subject or title of the event
    start_time: datetime  # The start time of the event
    end_time: datetime  # The end time of the event
    attendees: list[EmailStr]  # A list of attendees with their details
    join_url: str  # Video call link

    model_config = {"from_attributes": True}

    @field_validator("attendees", mode="before")
    @classmethod
    def split_newline_string(cls, value):
        if isinstance(value, str):
            return value.splitlines()  # Split by newline
        return value  # Return the value as-is if it's already a list
