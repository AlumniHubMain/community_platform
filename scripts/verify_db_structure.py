import asyncio
from sqlalchemy import inspector, text
from common_db.config import db_settings, schema
from common_db.db import DatabaseManager


async def verify_db_structure():
    settings = db_settings.db
    db = DatabaseManager(settings)

    async with db.session() as session:
        # Get all tables in our schema
        result = await session.execute(
            text(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{schema}'
        """)
        )
        tables = result.scalars().all()
        print("\nTables in schema:", schema)
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
                WHERE table_schema = '{schema}' 
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

        # Add verification for vacancy parsing table
        if not inspector.has_table('vacancy_raw_parsing_results'):
            print("Missing table: vacancy_raw_parsing_results")
            missing_tables = True


if __name__ == "__main__":
    asyncio.run(verify_db_structure())
