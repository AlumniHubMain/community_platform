from typing import Optional
from enum import Enum

from .broker import MessageBroker
from .google_pubsub import GooglePubSubBroker
from .nats import NatsBroker


class BrokerType(Enum):
    GOOGLE_PUBSUB = "google_pubsub"
    NATS = "nats"


def _create_google_pubsub_broker(project_id: Optional[str] = None, credentials: Optional[any] = None) -> GooglePubSubBroker:
    if project_id is None or credentials is None:
        raise ValueError("project_id and credentials required for Google PubSub")
    return GooglePubSubBroker(project_id=project_id, credentials=credentials)


def _create_nats_broker(**kwargs) -> NatsBroker:
    return NatsBroker()


class BrokerFactory:
    """
    BrokerFactory creates message broker instances based on the specified type.
    Supports Google PubSub and NATS (in future) implementations.

    Example:
        broker = BrokerFactory.create_broker(
            BrokerType.GOOGLE_PUBSUB,
            project_id="my-project",
            credentials=credentials
        )
    """
    _BROKER_CREATORS = {
        BrokerType.GOOGLE_PUBSUB: _create_google_pubsub_broker,
        BrokerType.NATS: _create_nats_broker,
    }

    @classmethod
    def create_broker(cls, broker_type: BrokerType, **kwargs) -> MessageBroker:
        creator = cls._BROKER_CREATORS.get(broker_type)
        if not creator:
            raise ValueError(f"Unknown broker type: {broker_type}")
        result = creator(**kwargs)
        if isinstance(result, Exception):
            raise result
        return result
