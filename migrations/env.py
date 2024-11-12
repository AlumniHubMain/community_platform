from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.db_proxy.common_db.config import settings
from backend.db_proxy.common_db.db_abstract import Base, schema
from tg_bot.src.staff.models import ORMTgBotStaff
from tg_bot.src.logging.models import ORMTgBotLoggingEvents


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option(name='sqlalchemy.url',
                       value=settings.database_url_asyncpg.get_secret_value() + '?async_fallback=True')

target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    """Функция для фильтрации схем."""
    if type_ == "schema":
        return name == schema  # Включает только нужную схему
    return True  # Включает все остальные объекты


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=schema,
        include_schemas=True,  # Включение всех схем
        include_name=include_name  # Фильтрация по имени схемы
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=schema,
            include_schemas=True,
            include_name=include_name
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
