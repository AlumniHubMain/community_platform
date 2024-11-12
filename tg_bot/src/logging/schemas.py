from datetime import datetime, UTC
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


class DTOUpdateBlockedStatus(BaseModel):
    telegram_id: int
    is_blocked: bool
    status_update_date: datetime = datetime.now(UTC)
