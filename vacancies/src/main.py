# Copyright 2024 Alumnihub

"""Main entry point for the vacancy links extraction process."""

import asyncio

from loguru import logger

from src.link_extractor.booking.extractor import BookingLinkExtractor


async def main() -> None:
    """Execute the vacancy links extraction process for different companies."""
    extractor = BookingLinkExtractor()
    links = await extractor.get_links()
    logger.info(f"Found {len(links)} unique vacancy links in Booking")
    for link in links:
        logger.info(link)


if __name__ == "__main__":
    asyncio.run(main())
