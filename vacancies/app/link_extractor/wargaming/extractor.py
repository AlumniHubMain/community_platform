# Copyright 2024 Alumnihub
"""Extractor for Wargaming vacancy links."""

import traceback

from loguru import logger
from playwright.async_api import Page

from app.link_extractor.base import BaseLinkExtractor


class WargamingLinkExtractor(BaseLinkExtractor):
    """Extractor for Wargaming vacancy links."""

    def __init__(self, logger: logger = logger) -> None:
        """Initialize the WargamingLinkExtractor."""
        super().__init__("https://wargaming.com/en/careers/", logger)

    @property
    def name(self) -> str:
        """Return the name of the extractor.

        Returns:
            str: The name of the extractor

        """
        return "Wargaming"

    async def _load_all_content(self, page: Page) -> None:
        """Load all vacancy content by handling pagination."""
        # Wait for the vacancy container to load
        try:
            await page.wait_for_selector(".careers-list", timeout=self.timeout)
        except Exception as e:  # noqa: BLE001
            self.logger.info("No vacancies found: {error}", error=e)
        try:
            await page.wait_for_load_state("networkidle")
        except Exception as e:  # noqa: BLE001
            self.logger.info("Network idle not found: {error}", error=e)

        while True:
            try:
                # Try to find and click the "Show more" button
                await page.locator(".show-more").click(timeout=5000)
                try:
                    await page.wait_for_load_state("networkidle")
                except Exception:  # noqa: BLE001
                    self.logger.info("Network idle not found", error=traceback.format_exc())
                await page.wait_for_timeout(2000)  # Add delay to ensure content loads

            except Exception:  # noqa: BLE001
                self.logger.info("Pagination completed or error occurred", error=traceback.format_exc())
                break

    async def _extract_links(self, page: Page) -> list[str]:  # noqa: PLR6301
        """Extract all vacancy links from the loaded page.

        Returns:
        list of links

        """
        return await page.eval_on_selector_all(
            ".job-list [data-reactid] a",
            "elements => elements.map(el => el.href)",
        )

    async def _cleanup(self) -> None:
        """Additional cleanup implementation."""
