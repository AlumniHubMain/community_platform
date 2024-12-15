from pydantic import BaseModel

import events_pb2
from ievent_converter import IEventConverter
from schemas import (
    MeetingInviteEvent,
    MeetingResponseEvent,
)


class ProtobufEventConverter(IEventConverter):
    def convert_notification(self, notification: BaseModel) -> bytes:
        protobuf = self.convert_to_protobuf(notification)
        return protobuf.SerializeToString()

    def convert_to_protobuf(self, event) -> events_pb2.Event:
        event_type = type(event)
        if event_type is MeetingInviteEvent:
            event_data = events_pb2.Event(
                event_type=events_pb2.eMeetingInvitation,
                initiator_id=event.inviter_id,
                recipient_id=event.invited_id,
                meeting_invitation=events_pb2.MeetingInvitationEvent(
                    meeting_id=event.meeting_id
                ),
            )
        elif event_type is MeetingResponseEvent:
            event_data = events_pb2.Event(
                event_type=events_pb2.eMeetingResponse,
                initiator_id=event.user_id,
                recipient_id=0,  # unspecified, send to organisers
                meeting_response=events_pb2.MeetingResponseEvent(
                    meeting_id=event.meeting_id
                ),
            )
        else:
            raise NotImplementedError(
                f"Message type '{event_type.__name__}' is not supported"
            )
        return event_data
