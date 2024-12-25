from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from .config import settings


schema: str = settings.db_schema


class Base(DeclarativeBase):
    """
    Базовая модель таблицы. Тут прописываем свойства, общие для всех таблиц.
    """

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


engine: AsyncEngine = create_async_engine(
    url=settings.database_url_asyncpg.get_secret_value()
)
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор асинхронной сессии. По-умолчанию может быть открыто 5 сессий (Pool_size=5 в engine)
    """
    async with session_maker() as session:
        yield session
