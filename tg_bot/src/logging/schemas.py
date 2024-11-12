from datetime import datetime
from pydantic import BaseModel
from .models import TgBotEventType


class DTOTgBotLoggingEvents(BaseModel):
    telegram_name: str | None = None
    telegram_id: int
    event_type: TgBotEventType
    event_name: str
    bot_state: str | None = None
    content: str | None = None
    chat_title: str | None = None
    chat_id: int
