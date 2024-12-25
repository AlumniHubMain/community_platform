import logging

from google.cloud import pubsub_v1
from google.protobuf.message import Message

from .emitter_interface import IProtoEmitter


class PubsubEventEmitter(IProtoEmitter):
    def __init__(self, topic: str = None):
        self.topic = topic

        if not self.topic:
            raise RuntimeError("A topic must be specified when using PubSub")

        self.publisher = pubsub_v1.PublisherClient()

    def emit(self, event: Message):
        res = self.publisher.publish(
            self.topic, data=event.SerializeToString()
        ).result()
        logging.info("Publish result: %s", res)

    @staticmethod
    def _log_event(event_data: str):
        logging.info(event_data)
