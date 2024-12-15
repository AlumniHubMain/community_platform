import logging

from google.cloud import pubsub_v1
from google.protobuf import json_format

from schemas import MeetingInviteEvent, MeetingResponseEvent
from protobuf_event_converter import ProtobufEventConverter


class PubsubEventEmitter:
    def __init__(self, topic: str = None):
        self.topic = topic

        if not self.topic:
            raise RuntimeError("A topic must be specified when using PubSub")

        self.converter = ProtobufEventConverter()
        self.publisher = pubsub_v1.PublisherClient()

    def emit(self, event: MeetingInviteEvent | MeetingResponseEvent):
        self._send_to_pubsub(self.converter.convert_notification(event))

    @staticmethod
    def _log_event(event_data: str):
        logging.info(event_data)

    def _send_to_pubsub(self, event_data: bytes):
        res = self.publisher.publish(self.topic, data=event_data).result()
        logging.info("Publish result: %s", res)
