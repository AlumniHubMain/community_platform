from abc import abstractmethod

from schemas import MeetingInviteEvent, MeetingResponseEvent


class IEventEmitter:
    @abstractmethod
    def emit(self, event: MeetingInviteEvent | MeetingResponseEvent):
        pass
