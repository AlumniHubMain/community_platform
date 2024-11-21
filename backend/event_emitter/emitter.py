import logging

from .schemas import MeetingInviteEvent, MeetingResponseEvent


class EventEmitter:
    def __init__(self, target: str = 'log', message_format: str = 'json'):
        self.target = target
        self.format = message_format

    def emit(self, event: MeetingInviteEvent | MeetingResponseEvent):
        # Serialize event based on the format
        if self.format == 'json':
            event_data = event.model_dump_json(indent=None)  # Convert to compact JSON
        else:
            raise NotImplementedError(f"Format '{self.format}' is not supported")

        # Handle target-specific logic
        if self.target == 'log':
            self._log_event(f'Would emit notification: {event_data}')
        elif self.target == 'pubsub':
            self._send_to_pubsub(event_data)
        else:
            raise NotImplementedError(f"Target '{self.target}' is not supported")

    @staticmethod
    def _log_event(event_data: str):
        logging.info(event_data)

    @staticmethod
    def _send_to_pubsub(event_data: str):
        raise NotImplementedError("PubSub not yet supported")
