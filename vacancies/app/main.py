# Copyright 2024 Alumnihub

"""Main entry point for the vacancy links extraction process."""

import asyncio
import os
import traceback
from urllib.parse import urljoin

from loguru import logger

from app.config import config, credentials
from app.data_extractor.processor import VacancyProcessor
from app.db import PostgresDB, PostgresSettings, VacancyRepository
from app.link_extractor import BaseLinkExtractor


async def main(logger: logger) -> None:
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

        for extractor in extractors:
            if hasattr(extractor, "close") and callable(extractor.close):
                await extractor.close()
            elif hasattr(extractor, "session") and hasattr(extractor.session, "close"):
                await extractor.session.close()

        # Initialize database and repository
        db = PostgresDB.create(
            settings=PostgresSettings(
                user=credentials.DB_USER,
                password=credentials.DB_PASS,
                database=credentials.DB_NAME,
                instance_connection_name=os.environ.get("INSTANCE_CONNECTION_NAME"),
                use_cloud_sql=True,
            ),
            logger=logger,
        )
        # db.drop_and_create_db_and_tables()

        repository = VacancyRepository(db)
        processor = VacancyProcessor(vacancy_repository=repository, logger=logger)
        # Process results
        for extractor, links in zip(extractors, results[:4], strict=False):
            if isinstance(links, Exception):
                logger.error(f"Error extracting links from {extractor.__class__.__name__}: {links}")
                continue

            company_name = extractor.name
            base_url = extractor.base_url
            logger.info(f"Found {len(links)} unique vacancy links in {company_name} ({base_url})")
            for link in links:
                full_link = urljoin(base_url, link)
                if not repository.exists_by_url(full_link):
                    await processor.add_url(full_link, company_name)
                    logger.info(f"put to queue new vacancy: {full_link}")
                else:
                    vacancy = repository.update_time_reachable_by_url(full_link)
                    logger.info(f"Updated vacancy {vacancy.id} in database")

        await processor.start()
        await processor.shutdown()

    except Exception:
        logger.error("Error in main: {error}", error=traceback.format_exc())

    finally:
        if db:
            db.close()

        logger.info("Ending the vacancy links extraction process")


if __name__ == "__main__":
    try:
        logger.info("Starting the vacancy links extraction process")
        asyncio.run(main(logger))
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
