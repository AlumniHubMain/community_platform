from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)
from config import DatabaseSettings

class DatabaseManager:
    def __init__(self, settings: DatabaseSettings):
        self.settings = settings
        self.engine: AsyncEngine = create_async_engine(
            url=settings.database_url_asyncpg.get_secret_value(),
            pool_size=5,
            max_overflow=10
        )
        self.session_maker = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_maker() as session:
            yield session 