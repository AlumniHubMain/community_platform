# Copyright 2024 Alumnihub

"""Main entry point for the vacancy links extraction process."""

import asyncio
import os
import sys
import traceback
from urllib.parse import urljoin

from loguru import logger

from app.config import GCP_LOG_FORMAT, config, credentials
from app.data_extractor.processor import VacancyProcessor
from app.db import PostgresDB, PostgresSettings, VacancyRepository
from app.link_extractor import BaseLinkExtractor


async def main(logger: logger) -> None:
    """Execute the vacancy links extraction process for different companies with concurrency limit."""
    semaphore = asyncio.Semaphore(config.CONCURRENT_EXTRACTIONS)
    db = None
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

        repository = VacancyRepository(db, logger=logger)
        processor = VacancyProcessor(
            vacancy_repository=repository,
            max_input_tokens=config.MAX_INPUT_TOKENS,
            max_output_tokens=config.MAX_OUTPUT_TOKENS,
            num_workers=config.NUM_WORKERS,
            logger=logger,
        )
        # Process results
        for extractor, links in zip(extractors, results, strict=False):
            if isinstance(links, Exception):
                logger.error("Error extracting links", extractor_name=extractor.name, error=traceback.format_exc())
                continue

            logger.info(
                "Found {num_links} unique vacancy links in {extractor_name} ({extractor_base_url})",
                num_links=len(links),
                extractor_name=extractor.name,
                extractor_base_url=extractor.base_url,
            )
            for link in links:
                full_link = urljoin(extractor.base_url, link)
                if not repository.exists_by_url(full_link):
                    await processor.add_url(full_link, extractor.name)
                    logger.info("Added new vacancy to queue", url=full_link, extractor_name=extractor.name)
                else:
                    vacancy = repository.update_time_reachable_by_url(full_link)
                    logger.info("Updated vacancy in database", vacancy_id=vacancy.id, url=full_link)

        await processor.start()
        await processor.shutdown()

    except Exception:
        logger.error("Error in main", error=traceback.format_exc())

    finally:
        if db:
            db.close()

        logger.info("Ending the vacancy links extraction process")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format=GCP_LOG_FORMAT,
        level=config.LOG_LEVEL,
        colorize=True,
    )
    logger.info("Starting vacancy links extraction process")
    asyncio.run(main(logger))
