from sqlalchemy import Column, DateTime, Index, String

from .base import ObjectTable
from common_db.config import schema


class ORMCallbotScheduledMeeting(ObjectTable):
    __tablename__ = 'callbot_scheduled_meetings'
    __table_args__ = (
        Index('ix_callbot_scheduled_meetings_google_id', 'google_id', unique=True),
        Index('ix_callbot_scheduled_meetings_start_time', 'start_time'),
        Index('ix_callbot_scheduled_meetings_end_time', 'end_time'),
        {'schema': schema},
    )

    google_id = Column(String, unique=True, nullable=False)  # The unique ID of the event from Google Calendar
    subject = Column(String, nullable=False)  # The subject or title of the event
    start_time = Column(DateTime(timezone=True), nullable=False)  # The start time of the event
    end_time = Column(DateTime(timezone=True), nullable=False)  # The end time of the event
    attendees = Column(String, nullable=False)  # list of attendees, one per line
    join_url = Column(String, nullable=False)  # Google Meet, Zoom, etc.
    callbot_id = Column(String, nullable=True) # The ID of the callbot that will join the meeting


class ORMCallbotEnabledUsers(ObjectTable):
    """
    List of users approved to invite a bot to a meeting
    """
    __tablename__ = 'callbot_enabled_users'
    email = Column(String, primary_key=True, nullable=False)
