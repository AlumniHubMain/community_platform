from enum import Enum as BaseEnum

from sqlalchemy import Enum, BigInteger
from sqlalchemy.orm import mapped_column, Mapped

from common_db.db_abstract import ObjectTable


class TgBotEventType(BaseEnum):
    message: str = 'message'
    callback: str = 'callback'


class ORMTgBotLoggingEvents(ObjectTable):
    """
    The model of the tg_bot_logging_events table in Postgres (logging event telegrams).
    """
    __tablename__ = 'tg_bot_logging_events'

    telegram_name: Mapped[str | None]
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    event_type: Mapped[TgBotEventType] = mapped_column(
        Enum(TgBotEventType, name='tg_event_type', inherit_schema=True)
    )
    event_name: Mapped[str]
    bot_state: Mapped[str | None]
    content: Mapped[str | None]
    chat_title: Mapped[str | None]
    chat_id: Mapped[int] = mapped_column(BigInteger)
