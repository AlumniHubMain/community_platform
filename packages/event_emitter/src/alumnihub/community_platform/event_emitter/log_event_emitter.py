import logging

from google.protobuf import json_format

from ievent_emitter import IEventEmitter
from schemas import MeetingInviteEvent, MeetingResponseEvent
from protobuf_event_converter import ProtobufEventConverter
from events_pb2 import Event


class LogEventEmitter(IEventEmitter):
    def emit(self, event: MeetingInviteEvent | MeetingResponseEvent):
        converted = ProtobufEventConverter().convert_notification(event)
        logging.info(json_format.MessageToJson(Event().ParseFromString(converted)))
