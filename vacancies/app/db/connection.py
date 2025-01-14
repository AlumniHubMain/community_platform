# Copyright 2024 Alumnihub
"""PostgreSQL connection module."""

import asyncio
import os
from collections.abc import AsyncGenerator

import asyncpg
from google.cloud.sql.connector import Connector, IPTypes
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .settings import PostgresSettings
from .vacancy_schema import Base


class PostgresDB:
    """PostgreSQL connection."""

    def __init__(self, settings: PostgresSettings, logger: logger = logger) -> None:
        """Initialize PostgreSQL connection parameters.

        Args:
            settings (PostgresSettings): Database connection settings
            logger (logger): Logger instance

        """
        self.settings = settings
        self.engine = None
        self.session_factory = None
        self.connector = None
        self.logger = logger

    @classmethod
    async def create(cls, settings: PostgresSettings, logger: logger = logger) -> "PostgresDB":
        """Create and initialize a new PostgresDB instance.

        Args:
            settings (PostgresSettings): Database connection settings
            logger (logger): Logger instance

        Returns:
            PostgresDB: Initialized database connection instance

        """
        db = cls(settings, logger)
        if db.settings.use_cloud_sql:
            db.engine = await db._create_cloud_sql_engine()  # noqa: SLF001
        else:
            db.engine = db._create_standard_engine()  # noqa: SLF001

        db.session_factory = async_sessionmaker(db.engine, class_=AsyncSession, expire_on_commit=False)
        return db

    def _create_standard_engine(self) -> None:
        """Create a standard engine."""
        database_url = f"postgresql+asyncpg://{self.settings.user}:{self.settings.password}@{self.settings.host}:{self.settings.port}/{self.settings.database}"
        return create_async_engine(
            database_url,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            echo=True,
        )

    async def _create_cloud_sql_engine(self) -> None:
        """Create a Cloud SQL engine."""
        ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

        loop = asyncio.get_running_loop()
        self.connector = Connector(loop=loop)

        async def getconn() -> asyncpg.Connection:
            """Get a connection to the database.

            Returns:
                asyncpg.Connection: A connection to the database

            """
            conn: asyncpg.Connection = await self.connector.connect_async(
                self.settings.instance_connection_name,
                "asyncpg",
                user=self.settings.user,
                password=self.settings.password,
                db=self.settings.database,
                ip_type=ip_type,
            )
            return conn

        return create_async_engine(
            "postgresql+asyncpg://",
            async_creator=getconn,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
        )

    def get_session(self) -> async_sessionmaker[AsyncSession]:
        """Get a session factory.

        Returns:
            async_sessionmaker[AsyncSession]: A session factory

        """
        return self.session_factory()

    async def get_session_ctx(self) -> AsyncGenerator[AsyncSession]:
        """Get a session context manager.

        Yields:
            AsyncGenerator[AsyncSession]: A session context manager.

        """
        async with self.session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    async def close(self) -> None:
        """Close the database connection."""
        if self.engine:
            try:
                # Dispose of the engine which will close all connections in the pool
                await self.engine.dispose()
            except Exception as e:
                self.logger.exception("Error disposing engine: {error}", error=e)

        if self.connector:
            try:
                # Set a shorter timeout for connector closure
                await asyncio.wait_for(self.connector.close(), timeout=5.0)
            except TimeoutError:
                self.logger.warning("Cloud SQL connector closure timed out, forcing cleanup")
                try:
                    if hasattr(self.connector, "_close_expired_connections"):
                        await self.connector._close_expired_connections()  # noqa: SLF001
                    if hasattr(self.connector, "_connections"):
                        await asyncio.gather(
                            *[conn.close() for conn in self.connector._connections],  # noqa: SLF001
                            return_exceptions=True,
                        )
                except Exception as e:
                    self.logger.exception("Error during forced connector cleanup: {error}", error=e)
            except Exception as e:
                self.logger.exception("Error closing Cloud SQL connector: {error}", error=e)
            finally:
                self.connector = None

    async def __aenter__(self) -> "PostgresDB":
        """Async context manager entry.

        Returns:
            PostgresDB: The database connection instance

        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        """Async context manager exit."""
        await self.close()

    async def drop_and_create_db_and_tables(self) -> None:
        """Drop and create all tables in the database."""
        engine = self.engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
