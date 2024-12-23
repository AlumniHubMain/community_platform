import logging

from google.protobuf import json_format

from .emitter_interface import IProtoEmitter
from google.protobuf.message import Message


logger = logging.getLogger(__name__)


class LogEventEmitter(IProtoEmitter):
    def emit(self, event: Message):
        logger.info(json_format.MessageToJson(event, indent=None))
