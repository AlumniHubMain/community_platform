from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict
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


class DTOCheckUserBlockedBot(BaseModel):
    telegram_id: int
    is_tg_bot_blocked: bool
    blocked_status_update_date: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
