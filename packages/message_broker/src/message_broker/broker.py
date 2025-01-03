from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Callable, TypeVar, Generic, Union, Awaitable


T = TypeVar('T')
SchemaType = TypeVar('SchemaType', bound=BaseModel)
MessageHandler = Union[Callable[[T], None], Callable[[T], Awaitable[None]]]


class MessageBroker(ABC, Generic[T]):
    """
    Message Broker is an abstract interface for working with message brokers.
    It supports publishing and subscribing to messages through different implementations (Google PubSub, NATS, etc.).

    Example:
    broker = BrokerFactory.create_broker(BrokerType.GOOGLE_PUBSUB,
                                         project_id="my-project",
                                         credentials=settings.ps_credentials)
    await broker.subscribe("my-topic-sub", message_handler)
    await broker.publish("my-topic", message)
    """
    @abstractmethod
    async def publish(self, topic: str, message: SchemaType) -> None:
        """
        Publishing a SchemaType (son of pydantic.BaseModel) message to the specified topic
        """
        pass

    @abstractmethod
    async def subscribe(self, sub_topic: str, callback: MessageHandler[T]) -> None:
        """
        Subscribing to a topic with a synchronous or asynchronous callback handler for type T messages
        """
        pass
