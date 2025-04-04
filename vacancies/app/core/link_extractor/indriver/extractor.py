# Copyright 2024 Alumnihub
"""Extractor for InDrive vacancy links."""

import asyncio
import traceback

from picologging import Logger
from playwright.async_api import Page

from app.core.link_extractor.base import BaseLinkExtractor


class IndriverLinkExtractor(BaseLinkExtractor):
    """Extractor for InDrive vacancy links."""

    def __init__(self, logger: Logger = Logger) -> None:
        """Initialize the InDriveLinkExtractor."""
        super().__init__("https://careers.indrive.com/vacancies", logger)

    @property
    def name(self) -> str:
        """Return the name of the extractor.

        Returns:
            str: The name of the extractor

        """
        return "InDrive"

    async def _load_all_content(self, page: Page) -> None:
        # Ждем загрузки основного контента
        try:
            await page.wait_for_selector("a[href*='/vacancies/']", timeout=self.timeout)
        except Exception:  # noqa: BLE001
            self.logger.info("No vacancies found on the page", extra={"error": traceback.format_exc()})

        # Нажимаем на кнопку "See more", пока она есть
        while True:
            try:
                see_more_button = await page.wait_for_selector("button:has-text('See more')", timeout=5000)
                await see_more_button.click()
                await asyncio.sleep(2)
            except Exception:  # noqa: BLE001
                self.logger.info(
                    "No more 'See more' button found, all vacancies loaded", extra={"error": traceback.format_exc()}
                )
                break

    async def _extract_links(self, page: Page) -> list[str]:  # noqa: PLR6301
        links = await page.eval_on_selector_all(
            "a[href*='/vacancies/']",
            "elements => elements.map(el => el.getAttribute('href'))",
        )
        return list(set(links))
