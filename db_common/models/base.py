from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from db_common.config import settings

schema: str = settings.db_schema


class Base(DeclarativeBase):
    """Base model for all tables"""

    __abstract__ = True


class ObjectTable(Base):
    """Template for objects with timestamps"""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=text("TIMEZONE('utc', now())"),
    )
