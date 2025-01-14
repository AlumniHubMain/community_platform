# Copyright 2024 Alumnihub

"""Main entry point for the vacancy links extraction process."""

import asyncio
import os
from datetime import UTC, datetime

from loguru import logger

from app.config import config, credentials
from app.db import PostgresDB, PostgresSettings, VacancyRepository
from app.link_extractor import BaseLinkExtractor


async def main() -> None:
    """Execute the vacancy links extraction process for different companies with concurrency limit."""
    semaphore = asyncio.Semaphore(config.CONCURRENT_EXTRACTIONS)
    db = None
    extractors = []
    try:
        # Initialize extractors from config
        extractors = [extractor_class(logger=logger) for extractor_class in config.EXTRACTORS.values()]

        async def extract_with_semaphore(extractor: BaseLinkExtractor) -> list[str]:
            async with semaphore:
                return await extractor.get_links()

        # Run extractors concurrently with semaphore limit
        results = await asyncio.gather(
            *[extract_with_semaphore(extractor) for extractor in extractors],
            return_exceptions=True,
        )

        # Initialize database and repository
        db = await PostgresDB.create(
            settings=PostgresSettings(
                user=credentials.DB_USER,
                password=credentials.DB_PASS,
                database=credentials.DB_NAME,
                instance_connection_name=os.environ.get("INSTANCE_CONNECTION_NAME"),
                use_cloud_sql=True,
            ),
            logger=logger,
        )
        await db.drop_and_create_db_and_tables()

        async with db.get_session() as session:
            repository = VacancyRepository(session)
            # Process results
            for extractor, links in zip(extractors, results, strict=False):
                if isinstance(links, Exception):
                    logger.error(f"Error extracting links from {extractor.__class__.__name__}: {links}")
                    continue

                company_name = extractor.name
                base_url = extractor.base_url
                logger.info(f"Found {len(links)} unique vacancy links in {company_name} ({base_url})")
                for link in links:
                    full_link = base_url + link
                    if not await repository.exists_by_url(full_link):
                        vacancy = await repository.add({
                            "url": full_link,
                            "company": company_name,
                        })
                        logger.info(f"Added vacancy {vacancy.id} to database")
                    else:
                        vacancy = await repository.update_time_reachable_by_url(
                            full_link,
                            {
                                "time_reachable": datetime.now(UTC),
                            },
                        )
                        logger.info(f"Updated vacancy {vacancy.id} in database")

    finally:
        # Cleanup extractors
        for extractor in extractors:
            if hasattr(extractor, "close") and callable(extractor.close):
                await extractor.close()
            elif hasattr(extractor, "session") and hasattr(extractor.session, "close"):
                await extractor.session.close()

        # Cleanup database
        if db:
            await db.close()

        logger.info("Ending the vacancy links extraction process")


if __name__ == "__main__":
    try:
        logger.info("Starting the vacancy links extraction process")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
