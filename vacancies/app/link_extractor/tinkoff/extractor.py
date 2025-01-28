"""Extractor for Tinkoff vacancy links."""

import traceback

from loguru import logger
from playwright.async_api import Page

from app.link_extractor.base import BaseLinkExtractor


class TinkoffLinkExtractor(BaseLinkExtractor):
    def __init__(self, logger: logger = logger) -> None:
        super().__init__("https://www.tbank.ru/career/vacancies/all/moscow/", logger)
        self.all_links = set()

    @property
    def name(self) -> str:
        return "Tinkoff"

    async def _load_all_content(self, page: Page) -> None:
        await page.wait_for_load_state("networkidle")  # Ensure initial content loads

        while True:
            try:
                # Wait for vacancy cards to appear
                await page.wait_for_selector(".VacancyCard__panel-desktop_aq6NiZ", timeout=self.timeout)

                # Extract links from current page
                current_links = await page.eval_on_selector_all(
                    ".VacancyCard__button-desktop_kq6NiZ a",  # Select links within the button
                    "elements => elements.map(el => el.href)",
                )
                self.all_links.update(current_links)

                self.logger.info(
                    "Found vacancies on current page",
                    current_links=len(current_links),
                    total_links=len(self.all_links),
                )

                # Find and click the "Show more" button
                show_more_button = await page.query_selector('button[data-qa-type="vc:show-more-btn"]')

                if not show_more_button:
                    self.logger.info("No more links on the pages available")
                    break

                await show_more_button.click()
                await page.wait_for_load_state("networkidle")  # Wait for new content
                await page.wait_for_timeout(2000)  # Add a small delay

            except Exception:  # noqa: BLE001
                self.logger.info("Error during pagination", error=traceback.format_exc())
                break

    async def _extract_links(self, page: Page) -> list[str]:  # noqa: ARG002
        return list(self.all_links)
