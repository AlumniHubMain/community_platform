import asyncio
from sqlalchemy import inspect, text
from db_common.config import DatabaseSettings
from db_common.db import DatabaseManager


async def verify_db_structure():
    settings = DatabaseSettings()
    db = DatabaseManager(settings)

    async with db.session() as session:
        # Get all tables in our schema
        result = await session.execute(
            text(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{settings.db_schema}'
        """)
        )
        tables = result.scalars().all()
        print("\nTables in schema:", settings.db_schema)
        print("=" * 50)
        for table in tables:
            print(f"\nTable: {table}")
            print("-" * 30)

            # Get column information for each table
            result = await session.execute(
                text(f"""
                SELECT 
                    column_name, 
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_schema = '{settings.db_schema}' 
                AND table_name = '{table}'
                ORDER BY ordinal_position
            """)
            )

            columns = result.fetchall()
            for col in columns:
                print(f"Column: {col[0]}")
                print(f"  Type: {col[1]}")
                print(f"  Nullable: {col[2]}")
                print(f"  Default: {col[3]}")
                print()


if __name__ == "__main__":
    asyncio.run(verify_db_structure())
