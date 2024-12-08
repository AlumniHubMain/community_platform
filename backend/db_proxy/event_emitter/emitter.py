import logging

from google.cloud import pubsub_v1
from google.protobuf import json_format

from common_db import config
from event_emitter.generated import events_pb2
from .schemas import MeetingInviteEvent, MeetingResponseEvent


class EventEmitter:
    def __init__(self, target: str = "log", message_format: str = "json"):
        self.target = target
        self.format = message_format

        if target == "pubsub":
            self.publisher = pubsub_v1.PublisherClient()

    def convert_to_protobuf(self, event) -> events_pb2.Event:
        event_type = type(event)
        if event_type is MeetingInviteEvent:
            event_data = events_pb2.Event(
                event_type=events_pb2.eMeetingInvitation,
                initiator_id=event.inviter_id,
                recipient_id=event.invited_id,
                meeting_invitation=events_pb2.MeetingInvitationEvent(meeting_id=event.meeting_id),
            )
        elif event_type is MeetingResponseEvent:
            event_data = events_pb2.Event(
                event_type=events_pb2.eMeetingResponse,
                initiator_id=event.user_id,
                recipient_id=0,  # unspecified, send to organisers
                meeting_response=events_pb2.MeetingResponseEvent(meeting_id=event.meeting_id),
            )
        else:
            raise NotImplementedError(f"Message type '{event_type.__name__}' is not supported")
        return event_data

    def emit(self, event: MeetingInviteEvent | MeetingResponseEvent):
        # Serialize event based on the format
        if self.format == "json":
            event_data = event.model_dump_json(indent=None)  # Convert to compact JSON
        elif self.format == "protobuf_json":
            event_data = json_format.MessageToJson(self.convert_to_protobuf(event)).encode()
        elif self.format == "protobuf_binary":
            event_data = self.convert_to_protobuf(event).SerializeToString()
        else:
            raise NotImplementedError(f"Format '{self.format}' is not supported")

        # Handle target-specific logic
        if self.target == "log":
            self._log_event(f"Would emit notification: {event_data}")
        elif self.target == "pubsub":
            self._send_to_pubsub(event_data)
        else:
            raise NotImplementedError(f"Target '{self.target}' is not supported")

    @staticmethod
    def _log_event(event_data: str):
        logging.info(event_data)

    def _send_to_pubsub(self, event_data: bytes):
        res = self.publisher.publish(config.settings.google_pubsub_notification_topic, data=event_data).result()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    e = EventEmitter(target="log", message_format="protobuf_binary")
    e.emit(MeetingInviteEvent(inviter_id=123, invited_id=321, meeting_id=333))
