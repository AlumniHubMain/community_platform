# Copyright 2024 Alumnihub
"""Extractor for Wargaming vacancy links."""
import asyncio

from playwright.async_api import Page

from src.link_extractor.base import BaseLinkExtractor


class WargamingLinkExtractor(BaseLinkExtractor):
    """Extractor for Wargaming vacancy links."""

    def __init__(self) -> None:
        """Initialize the WargamingLinkExtractor."""
        super().__init__("https://wargaming.com/en/careers/")

    async def _accept_cookies(self, page: Page) -> None:
        try:
            await page.click("button#onetrust-accept-btn-handler")
        except Exception as e:  # noqa: BLE001
            self.logger.info("No cookie consent button found: %s", e)

    async def _load_all_content(self, page: Page) -> None:
        # Ждем загрузки основного контента
        await page.wait_for_selector("a[href*='/careers/vacancy_']", timeout=self.timeout)

        # Нажимаем на кнопку "Show more", пока она есть
        while True:
            try:
                show_more_button = await page.wait_for_selector("span:has-text('Show more')", timeout=5000)
                await show_more_button.click()
                await asyncio.sleep(2)
            except Exception as e:  # noqa: BLE001
                self.logger.info("No more 'Show more' button found, all vacancies loaded: %s", e)
                break

    async def _extract_links(self, page: Page) -> list[str]:  # noqa: PLR6301
        return await page.eval_on_selector_all(
            "a[href*='/careers/vacancy_']", "elements => elements.map(el => el.getAttribute('href'))",
        )
