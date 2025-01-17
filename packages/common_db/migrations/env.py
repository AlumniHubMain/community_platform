from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
import alembic
from alembic import context

from common_db.config import db_settings
from common_db.models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set SQLAlchemy URL from settings
db_host = db_settings.db.db_host.get_secret_value()
# This is a hack to make migrations work both from local and from container
if db_host == 'db':
    url = db_settings.db.database_url_asyncpg.get_secret_value().replace("postgresql+asyncpg", "postgresql+psycopg2").replace("@db:", "@localhost:")
else:
    url = db_settings.db.database_url_asyncpg.get_secret_value().replace("postgresql+asyncpg", "postgresql+psycopg2")
config.set_main_option(
    "sqlalchemy.url",
    url,
)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    """Filter schemas to include"""
    if type_ == "schema":
        return name in [db_settings.db.db_schema]
    return True


def create_schema_if_not_exists(connection):
    """Create schema if it doesn't exist"""
    schema_name = db_settings.db.db_schema
    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
    connection.commit()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        version_table_schema=db_settings.db.db_schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Create schema before running migrations
        create_schema_if_not_exists(connection)
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            version_table_schema=db_settings.db.db_schema,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
