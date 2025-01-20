from pydantic import BaseModel, EmailStr
from datetime import datetime


class Event(BaseModel):
    google_id: str  # The unique ID of the event from Google Calendar
    subject: str  # The subject or title of the event
    start_time: datetime  # The start time of the event
    end_time: datetime  # The end time of the event
    attendees: list[EmailStr]  # A list of attendees with their details
