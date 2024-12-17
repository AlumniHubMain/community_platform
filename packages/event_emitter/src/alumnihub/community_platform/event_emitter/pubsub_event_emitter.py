import logging

from google.cloud import pubsub_v1

from . import events_pb2


class PubsubEventEmitter:
    def __init__(self, topic: str = None):
        self.topic = topic

        if not self.topic:
            raise RuntimeError("A topic must be specified when using PubSub")

        self.publisher = pubsub_v1.PublisherClient()

    def emit(self, event: events_pb2.Event):
        res = self.publisher.publish(self.topic, data=event.SerializeToString()).result()
        logging.info("Publish result: %s", res)

    @staticmethod
    def _log_event(event_data: str):
        logging.info(event_data)
