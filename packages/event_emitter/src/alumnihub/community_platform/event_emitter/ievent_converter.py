from abc import abstractmethod

from pydantic import BaseModel


class IEventConverter:
    @abstractmethod
    def convert_notification(self, notification: BaseModel) -> bytes:
        pass
