from typing import Callable, TypeVar

from .broker import MessageBroker

NatsMessageType = TypeVar('NatsMessageType')


class NatsBroker(MessageBroker[NatsMessageType]):
    def __init__(self):
        pass

    async def publish(self, topic: str, message: NatsMessageType) -> None:
        pass

    async def subscribe(self, topic: str, callback: Callable[[NatsMessageType], None]) -> None:
        pass
