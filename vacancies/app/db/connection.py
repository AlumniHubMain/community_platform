# Copyright 2024 Alumnihub
"""PostgreSQL connection module."""

import os
import traceback

from google.cloud.sql.connector import Connector, IPTypes
from picologging import Logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .settings import PostgresSettings
from .vacancy_schema import Base


class PostgresDB:
    """PostgreSQL connection."""

    def __init__(self, settings: PostgresSettings, logger: Logger = Logger) -> None:
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
    def create(cls, settings: PostgresSettings, logger: Logger = Logger) -> "PostgresDB":
        """Create and initialize a new PostgresDB instance.

        Args:
            settings (PostgresSettings): Database connection settings
            logger (logger): Logger instance

        Returns:
            PostgresDB: Initialized database connection instance

        """
        db = cls(settings, logger)
        if db.settings.use_cloud_sql:
            db.engine = db._create_cloud_sql_engine()
        else:
            db.engine = db._create_standard_engine()

        db.session_factory = sessionmaker(bind=db.engine, class_=Session, expire_on_commit=False)
        return db

    def _create_standard_engine(self) -> None:
        """Create a standard engine."""
        database_url = f"postgresql://{self.settings.user}:{self.settings.password}@{self.settings.host}:{self.settings.port}/{self.settings.database}"
        return create_engine(
            database_url,
            pool_size=10,
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=1800,
            echo=True,
        )

    def _create_cloud_sql_engine(self) -> None:
        """Create a Cloud SQL engine."""
        ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

        self.connector = Connector()

        def getconn():
            """Get a connection to the database."""
            conn = self.connector.connect(
                self.settings.instance_connection_name,
                "pg8000",
                user=self.settings.user,
                password=self.settings.password,
                db=self.settings.database,
                ip_type=ip_type,
            )
            return conn

        return create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_size=10,
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=1800,
        )

    def get_session(self) -> Session:
        """Get a database session."""
        return self.session_factory()

    def close(self) -> None:
        """Close the database connection."""
        try:
            if self.engine:
                self.engine.dispose()
        except Exception:
            self.logger.exception({
                "message": "Error disposing engine",
                "error": traceback.format_exc(),
            })

        try:
            if self.connector:
                self.connector.close()
                self.connector = None
        except Exception:
            self.logger.exception({
                "message": "Error closing Cloud SQL connector",
                "error": traceback.format_exc(),
            })

    def __enter__(self) -> "PostgresDB":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        """Context manager exit."""
        self.close()

    def drop_and_create_db_and_tables(self) -> None:
        """Drop and create all tables in the database."""
        engine = self.engine
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
