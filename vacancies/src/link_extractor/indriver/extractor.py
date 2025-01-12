# Copyright 2024 Alumnihub
"""Extractor for InDrive vacancy links."""

import asyncio

from playwright.async_api import Page

from src.link_extractor.base import BaseLinkExtractor


class InDriveLinkExtractor(BaseLinkExtractor):
    """Extractor for InDrive vacancy links."""

    def __init__(self) -> None:
        """Initialize the InDriveLinkExtractor."""
        super().__init__("https://careers.indrive.com/vacancies")

    async def _accept_cookies(self, page: Page) -> None:
        try:
            await page.click("button#onetrust-accept-btn-handler")
        except Exception as e:  # noqa: BLE001
            self.logger.info("No cookie consent button found: %s", e)

    async def _load_all_content(self, page: Page) -> None:
        # Ждем загрузки основного контента
        await page.wait_for_selector("a[href*='/vacancies/']", timeout=self.timeout)

        # Нажимаем на кнопку "See more", пока она есть
        while True:
            try:
                see_more_button = await page.wait_for_selector("button:has-text('See more')", timeout=5000)
                await see_more_button.click()
                await asyncio.sleep(2)
            except Exception as e:  # noqa: BLE001
                self.logger.info("No more 'See more' button found, all vacancies loaded: %s", e)
                break

    async def _extract_links(self, page: Page) -> list[str]:  # noqa: PLR6301
        links = await page.eval_on_selector_all(
            "a[href*='/vacancies/']", "elements => elements.map(el => el.getAttribute('href'))",
        )
        return list(set(links))
