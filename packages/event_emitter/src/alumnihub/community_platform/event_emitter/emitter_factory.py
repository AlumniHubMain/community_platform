from .emitter_interface import IProtoEmitter
from .pubsub_event_emitter import PubsubEventEmitter
from .log_event_emitter import LogEventEmitter


class EmitterFactory:
    @staticmethod
    def create_event_emitter(target: str, topic: str = None) -> IProtoEmitter:
        if target == "log":
            return LogEventEmitter()
        if target == "pubsub":
            if not topic:
                raise ValueError("topic cannot be None")
            return PubsubEventEmitter(topic=topic)
        raise ValueError("target must be 'log' or 'pubsub'")
