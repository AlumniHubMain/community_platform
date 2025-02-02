# Copyright 2024 Alumnihub
"""Settings for the database."""

from pydantic import BaseModel


class PostgresSettings(BaseModel):
    """Settings for the Postgres database."""

    host: str | None = None
    port: int | None = None
    database: str
    user: str
    password: str
    instance_connection_name: str | None = None
    use_cloud_sql: bool = False
