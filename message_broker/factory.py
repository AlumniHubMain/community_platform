from enum import Enum

from .broker import MessageBroker
from .google_pubsub import GooglePubSubBroker
from .nats import NatsBroker


class BrokerType(Enum):
    GOOGLE_PUBSUB = "google_pubsub"
    NATS = "nats"


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
        BrokerType.GOOGLE_PUBSUB: lambda kwargs: (
            GooglePubSubBroker(project_id=kwargs.get("project_id"),
                               credentials=kwargs.get("credentials"))
            if "project_id" and "credentials" in kwargs
            else ValueError("project_id and credentials required for Google PubSub")
        ),
        BrokerType.NATS: lambda kwargs: NatsBroker()
    }

    @classmethod
    def create_broker(cls, broker_type: BrokerType, **kwargs) -> MessageBroker:
        creator = cls._BROKER_CREATORS.get(broker_type)
        if not creator:
            raise ValueError(f"Unknown broker type: {broker_type}")
        result = creator(kwargs)
        if isinstance(result, Exception):
            raise result
        return result
