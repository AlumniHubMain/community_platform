import logging

from google.protobuf import json_format

from .ievent_emitter import IEventEmitter
from . import events_pb2


class LogEventEmitter(IEventEmitter):
    def emit(self, event: events_pb2.Event):
        logging.info(json_format.MessageToJson(event, indent=None))
