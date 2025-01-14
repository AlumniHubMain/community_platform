from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from common_db.config import schema

class Base(DeclarativeBase):
    """
    Базовая модель таблицы. Тут прописываем свойства, общие для всех таблиц.
    """

    __abstract__ = True
    __table_args__ = {"schema": f"{schema}"}


class ObjectTable(Base):
    """
    Модель таблицы (шаблон) для объектов.
    """

    __abstract__ = True
    __allow_unmapped__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())")
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=text("TIMEZONE('utc', now())"),
    )
