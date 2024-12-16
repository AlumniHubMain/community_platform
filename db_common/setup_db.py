import os
from alembic.config import Config
from alembic import command
from sqlalchemy import text
from db_common.config import settings
from db_common.db import DatabaseManager
import asyncio


async def create_schema_if_not_exists(db: DatabaseManager):
    """Create schema if it doesn't exist"""
    async with db.session() as session:
        await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema}"))
        await session.commit()


async def insert_sample_data(db: DatabaseManager):
    """Insert sample data after migrations"""
    async with db.session() as session:
        # Insert sample users
        await session.execute(
            text(
                """
            INSERT INTO users (name, surname, email, avatars, about, interests, 
                             linkedin_link, telegram_name, telegram_id, expertise_area, 
                             grade, current_company, location, referral, is_tg_bot_blocked)
            VALUES 
            ('John', 'Doe', 'john.doe@example.com', ARRAY['avatar1.jpg', 'avatar2.jpg'], 
             'Senior Software Engineer', ARRAY['interest1'], 'https://linkedin.com/in/johndoe', 
             'johndoe', 123456789, ARRAY['development'], 'grade2', 'Tech Corp', 
             'london_uk', true, false)
            ON CONFLICT DO NOTHING
        """
            )
        )

        # Add more sample data inserts as needed...
        await session.commit()


def setup_database():
    """Set up database using Alembic migrations"""
    # Get the directory containing this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)

    # Create Alembic configuration
    alembic_cfg = Config(os.path.join(project_dir, "alembic.ini"))

    # Create schema if it doesn't exist
    db = DatabaseManager(settings)
    asyncio.run(create_schema_if_not_exists(db))

    # Run migrations
    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    setup_database()
