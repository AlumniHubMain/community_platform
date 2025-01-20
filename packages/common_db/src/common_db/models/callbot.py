from sqlalchemy import Column, DateTime, String

from .base import ObjectTable


class ORMCallbotScheduledMeeting(ObjectTable):
    __tablename__ = 'callbot_scheduled_meetings'

    google_id = Column(String, primary_key=True, nullable=False)  # The unique ID of the event from Google Calendar
    subject = Column(String, nullable=False)  # The subject or title of the event
    start_time = Column(DateTime, nullable=False)  # The start time of the event
    end_time = Column(DateTime, nullable=False)  # The end time of the event
    attendees = Column(String, primary_key=False, nullable=False)  # list of attendees, one per line
    join_url = Column(String, nullable=False)  # Google Meet, Zoom, etc.


class ORMCallbotEnabledUsers(ObjectTable):
    """
    List of users approved to invite a bot to a meeting
    """
    __tablename__ = 'callbot_enabled_users'
    email = Column(String, primary_key=True, nullable=False)
