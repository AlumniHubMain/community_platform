from abc import abstractmethod

from google.protobuf.message import Message

class IProtoEmitter:
    @abstractmethod
    def emit(self, event: Message):
        pass
