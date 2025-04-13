# Copyright 2024 Alumnihub
"""Extractor for Booking vacancy links."""

import traceback

from picologging import Logger
from playwright.async_api import Page

from app.core.link_extractor.base import BaseLinkExtractor


class BookingLinkExtractor(BaseLinkExtractor):
    """Extractor for Booking vacancy links."""

    def __init__(self, logger: Logger = Logger) -> None:
        """Initialize the BookingLinkExtractor."""
        super().__init__("https://jobs.booking.com/booking/jobs", logger)
        self.all_links = set()

    @property
    def name(self) -> str:
        """Return the name of the extractor.

        Returns:
            str: The name of the extractor

        """
        return "Booking"

    async def _load_all_content(self, page: Page) -> None:
        try:
            await page.wait_for_selector('a[href*="/booking/jobs/"]', timeout=self.timeout)
        except Exception:
            self.logger.info(
                {
                    "message": "Timeout while loading content",
                    "error": traceback.format_exc(),
                    "extractor_name": self.name,
                },
            )

        while True:
            current_links = await page.eval_on_selector_all(
                'a[href*="/booking/jobs/"]',
                "elements => elements.map(el => el.getAttribute('href'))",
            )
            self.all_links.update(current_links)
            self.logger.info(
                "Found vacancies on current page",
                current_links=len(current_links),
                total_links=len(self.all_links),
            )

            try:
                next_button = await page.query_selector(
                    "button.mat-focus-indicator.mat-tooltip-trigger"
                    ".mat-paginator-navigation-next.mat-icon-button"
                    ".mat-button-base",
                )

                if not next_button or await next_button.is_disabled():
                    self.logger.info("No more links on the pages available", extra={"extractor_name": self.name})
                    break

                await next_button.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
            except Exception:  # noqa: BLE001
                self.logger.info(
                    {
                        "message": "Error during pagination",
                        "error": traceback.format_exc(),
                        "extractor_name": self.name,
                    },
                )
                break

    async def _extract_links(self, page: Page) -> list[str]:  # noqa: ARG002
        """Extract links from the page."""
        links = list(getattr(self, "all_links", set()))
        self.logger.info(
            {
                "message": "Extracted links",
                "extractor_name": self.name,
                "total_links_count": len(links),
            },
        )
        return links
