# Copyright 2024 Alumnihub

"""Main entry point for the vacancy links extraction process."""

import asyncio

from loguru import logger

from app.link_extractor import BookingLinkExtractor, InDriveLinkExtractor, WargamingLinkExtractor


async def main() -> None:
    """Execute the vacancy links extraction process for different companies."""
    extractor = WargamingLinkExtractor()
    links = await extractor.get_links()
    logger.info(f"Found {len(links)} unique vacancy links in Wargaming")
    for link in links:
        logger.info(link)

    extractor = InDriveLinkExtractor()
    links = await extractor.get_links()
    logger.info(f"Found {len(links)} unique vacancy links in InDrive")
    for link in links:
        logger.info(link)

    extractor = BookingLinkExtractor()
    links = await extractor.get_links()
    logger.info(f"Found {len(links)} unique vacancy links in Booking")
    for link in links:
        logger.info(link)


if __name__ == "__main__":
    logger.info("Starting the vacancy links extraction process")
    asyncio.run(main())
