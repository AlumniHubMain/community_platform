import os
from typing import AsyncGenerator
from alembic.config import Config
from alembic import command
from sqlalchemy import text
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)

from common_db.config import db_settings as settings
import asyncio



class DatabaseManager:
    def __init__(self, settings):
        self.settings = settings        
        self.engine: AsyncEngine = create_async_engine(
            url=settings.database_url_asyncpg.get_secret_value(), pool_size=5, max_overflow=10
        )
        self.session_maker = async_sessionmaker(bind=self.engine, expire_on_commit=False)

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


async def create_schema_if_not_exists(db: DatabaseManager):
    """Create schema if it doesn't exist"""
    async with db.session() as session:
        await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.db.db_schema}"))
        await session.commit()


def setup_database():
    """Set up database using Alembic migrations"""
    # Get the directory containing this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)

    # Create Alembic configuration
    alembic_cfg = Config(os.path.join(project_dir, "alembic.ini"))

    # Create schema if it doesn't exist
    db = DatabaseManager(settings.db)
    
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(create_schema_if_not_exists(db))
    finally:    
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

    # Run migrations
    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    setup_database()
