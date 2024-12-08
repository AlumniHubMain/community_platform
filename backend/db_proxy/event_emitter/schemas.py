from pydantic import BaseModel


class EventData(BaseModel):
    pass


class MeetingInviteEvent(EventData):
    inviter_id: int  # ID of the person inviting
    invited_id: int  # ID of the person being invited
    meeting_id: int  # ID of the meeting

    def to_event(self):
        return Event(event_type="meeting_invite", data=self)


class MeetingResponseEvent(EventData):
    user_id: int  # ID of the person responding
    meeting_id: int  # ID of the meeting

    def to_event(self):
        return Event(event_type="meeting_response", data=self)


class Event(BaseModel):
    event_type: str
    data: EventData
