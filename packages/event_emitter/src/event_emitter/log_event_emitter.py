import logging

from google.protobuf import json_format

from .emitter_interface import IProtoEmitter
from google.protobuf.message import Message


class LogEventEmitter(IProtoEmitter):
    def emit(self, event: Message):
        logging.info(json_format.MessageToJson(event, indent=None))
