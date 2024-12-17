from abc import abstractmethod

from . import events_pb2


class IEventEmitter:
    @abstractmethod
    def emit(self, event: events_pb2.Event):
        pass
