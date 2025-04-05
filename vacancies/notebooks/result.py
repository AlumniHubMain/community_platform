import traceback

from picologging import Logger
from playwright.async_api import Page, TimeoutError

from app.core.link_extractor import BaseLinkExtractor

# Assuming BaseLinkExtractor is defined in app.link_extractor.base
# If not, you might need to define a simple base class or remove the inheritance

logger = Logger(__name__)


class TinkoffLinkExtractor(BaseLinkExtractor):
    """
    Extractor for T-Bank (Tinkoff) career vacancies page.
    Handles dynamic loading by clicking the "Показать еще" (Show More) button.
    """

    def __init__(self, logger: Logger = Logger(__name__)) -> None:
        # Using the specific Moscow URL from the example HTML
        super().__init__("https://www.tbank.ru/career/vacancies/all/moscow/", logger)
        self.all_links = set()
        # Selector for the individual vacancy links within the cards
        self._link_selector = 'div.AtomVacanciesCards__card_aIM3Uu a[href^="/career/"]'
        # Selector for the "Show More" button
        self._show_more_button_selector = 'button[data-qa-type="vc:show-more-btn"]'

    @property
    def name(self) -> str:
        return "Tinkoff"

    async def _load_all_content(self, page: Page) -> None:
        """
        Loads initial content and clicks the "Show More" button until it disappears
        or is no longer clickable, collecting links from each loaded batch.
        """
        self.logger.info("Waiting for initial vacancy links to load...")
        try:
            await page.wait_for_selector(self._link_selector, timeout=self.timeout)
            self.logger.info("Initial content loaded.")
        except TimeoutError:
            self.logger.warning("Timeout waiting for initial vacancy links. Page might be empty or structure changed.")
            return  # No content to load further

        while True:
            # Extract links currently visible on the page
            current_links = await page.eval_on_selector_all(
                self._link_selector,
                "elements => elements.map(el => el.getAttribute('href'))",
            )
            new_links_count = len(set(current_links) - self.all_links)
            self.all_links.update(current_links)
            self.logger.info(
                f"Found {new_links_count} new vacancies on current view. Total unique links: {len(self.all_links)}"
            )

            # Check for the "Show More" button
            try:
                show_more_button = await page.query_selector(self._show_more_button_selector)

                if not show_more_button or await show_more_button.is_hidden() or await show_more_button.is_disabled():
                    self.logger.info(
                        "No 'Show More' button found or it's hidden/disabled. Assuming all vacancies are loaded."
                    )
                    break

                self.logger.info("Clicking 'Show More' button...")
                await show_more_button.click()

                # Wait for new content to load - networkidle is often good for AJAX
                # Add a small timeout for safety
                await page.wait_for_load_state(
                    "networkidle", timeout=self.timeout / 2
                )  # Shorter timeout for subsequent loads
                await page.wait_for_timeout(2000)  # Extra buffer

            except TimeoutError:
                self.logger.warning(
                    "Timeout waiting for network idle after clicking 'Show More'. Proceeding, but some links might be missed."
                )
                # Decide whether to break or continue - continuing might lead to partial data
                break
            except Exception:
                self.logger.error(f"Error during pagination: {traceback.format_exc()}")
                break

    async def _extract_links(self, page: Page) -> list[str]:
        """
        Returns the unique links collected during the loading process.
        The base class will handle making them absolute.
        """
        # page argument is kept for consistency with the base class, though not used here
        # as links are collected in _load_all_content
        return list(self.all_links)


# Example usage (requires playwright and asyncio context)
# async def main():
#     from playwright.async_api import async_playwright
#     from loguru import logger
#
#     async with async_playwright() as p:
#         browser = await p.chromium.launch()
#         page = await browser.new_page()
#         try:
#             await page.goto("https://www.tbank.ru/career/vacancies/all/moscow/", wait_until="domcontentloaded")
#             extractor = TinkoffLinkExtractor(logger=logger)
#             links = await extractor.extract_links(page)
#             logger.info(f"Extracted {len(links)} links:")
#             for link in links:
#                 logger.info(link)
#         except Exception as e:
#             logger.error(f"An error occurred: {e}")
#         finally:
#             await browser.close()
#
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
