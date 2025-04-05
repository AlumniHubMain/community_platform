# Copyright 2024 Alumnihub
"""Extractor for Wargaming vacancy links."""

import traceback

from picologging import Logger
from playwright.async_api import Page

from app.core.link_extractor.base import BaseLinkExtractor


class WargamingLinkExtractor(BaseLinkExtractor):
    """Extractor for Wargaming vacancy links."""

    def __init__(self, logger: Logger = Logger) -> None:
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
        except Exception:  # noqa: BLE001
            self.logger.info(
                {
                    "message": "No vacancies found",
                    "error": traceback.format_exc(),
                    "extractor_name": self.name,
                },
            )
        try:
            await page.wait_for_load_state("networkidle")
        except Exception:  # noqa: BLE001
            self.logger.info(
                {
                    "message": "Network idle not found",
                    "error": traceback.format_exc(),
                    "extractor_name": self.name,
                },
            )

        while True:
            try:
                # Try to find and click the "Show more" button
                await page.locator(".show-more").click(timeout=5000)
                try:
                    await page.wait_for_load_state("networkidle")
                except Exception:  # noqa: BLE001
                    self.logger.info(
                        {
                            "message": "Network idle not found",
                            "error": traceback.format_exc(),
                            "extractor_name": self.name,
                        },
                    )
                await page.wait_for_timeout(2000)  # Add delay to ensure content loads

            except Exception:  # noqa: BLE001
                self.logger.info(
                    {
                        "message": "Pagination completed or error occurred",
                        "error": traceback.format_exc(),
                        "extractor_name": self.name,
                    },
                )
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
