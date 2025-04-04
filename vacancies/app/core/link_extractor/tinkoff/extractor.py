"""Extractor for Tinkoff vacancy links."""

import traceback
from urllib.parse import urljoin

from picologging import Logger
from playwright.async_api import Page

from app.core.link_extractor.base import BaseLinkExtractor


class TinkoffLinkExtractor(BaseLinkExtractor):
    """
    Extracts vacancy links from the Tinkoff (T-Bank) career page.
    Handles dynamic loading by clicking the 'Show More' button.
    """

    def __init__(self, logger: Logger = Logger) -> None:
        # Using the specific Moscow vacancies page as the base URL
        super().__init__("https://www.tbank.ru/career/vacancies/all/moscow/", logger)
        self.all_links = set()
        # Selector for individual vacancy links within cards
        self.link_selector = 'div.AtomVacanciesCards__card_aIM3Uu a[data-qa-type="uikit/button"][href^="/career/"]'
        # Selector for the "Show More" button
        self.show_more_button_selector = 'button[data-qa-type="vc:show-more-btn"]'
        # Selector to wait for initial cards to ensure the main content area is loaded
        self.initial_card_selector = "div.AtomVacanciesCards__card_aIM3Uu"

    @property
    def name(self) -> str:
        """Returns the name of the extractor."""
        return "Tinkoff"  # Or T-Bank, depending on preference

    async def _load_all_content(self, page: Page) -> None:
        """
        Loads all vacancy cards by repeatedly clicking the 'Show More' button
        until it's no longer available or visible/enabled.
        """
        try:
            # Wait for the first batch of vacancy cards to appear
            await page.wait_for_selector(self.initial_card_selector, timeout=self.timeout)
            self.logger.info("Initial vacancy cards loaded.")
        except TimeoutError:
            self.logger.warning(
                "Timeout waiting for initial vacancy cards. "
                "Page might be empty, structure changed, or took too long to load."
            )
            return  # Exit if initial content doesn't load

        while True:
            # Extract links visible in the current view
            # Use try-except in case the selector doesn't find elements temporarily
            try:
                current_links = await page.eval_on_selector_all(
                    self.link_selector,
                    "elements => elements.map(el => el.getAttribute('href'))",
                )
                new_links_count = len(set(current_links) - self.all_links)
                self.all_links.update(current_links)
                self.logger.info(
                    f"Found {new_links_count} new vacancies on current view. "
                    f"Total unique relative links: {len(self.all_links)}"
                )
            except Exception as e:
                self.logger.warning(f"Could not extract links from current view: {e}")
                # Decide whether to break or continue based on the error if needed
                # For now, we'll try to find the 'Show More' button anyway

            try:
                show_more_button = await page.query_selector(self.show_more_button_selector)

                # Check if the button exists AND is visible AND enabled.
                # is_visible() is important because the button might remain in DOM but hidden.
                if (
                    not show_more_button
                    or not await show_more_button.is_visible()
                    or not await show_more_button.is_enabled()
                ):
                    self.logger.info("No more 'Show More' button available or it's hidden/disabled. Finished loading.")
                    break

                self.logger.info("Clicking 'Show More' button...")
                await show_more_button.click()

                # Wait for network activity to settle after the click
                # Use a slightly shorter timeout for subsequent loads if desired
                await page.wait_for_load_state("networkidle", timeout=max(10000, self.timeout // 2))
                # Add a small delay to allow potential JS rendering after network idle
                await page.wait_for_timeout(1500)

            except TimeoutError:
                self.logger.warning(
                    "Timeout waiting for network idle after clicking 'Show More'. Assuming loading finished."
                )
                break  # Stop if loading takes too long after a click
            except Exception:
                self.logger.error(f"Error during 'Show More' pagination: {traceback.format_exc()}")
                break  # Stop on unexpected errors during pagination

    async def _extract_links(self, page: Page) -> list[str]:
        """
        Extracts the unique vacancy links collected during the loading process
        and converts them to absolute URLs.
        """
        # The base class's get_links method should ensure _load_all_content runs first.
        # Convert collected relative links to absolute URLs
        absolute_links = set()
        for link in self.all_links:
            if link:  # Ensure link is not empty
                try:
                    absolute_link = urljoin(self.base_url, link)
                    absolute_links.add(absolute_link)
                except ValueError:
                    self.logger.warning(f"Could not create absolute URL for: {link}")

        self.logger.info(f"Extracted {len(absolute_links)} unique absolute vacancy links.")
        return list(absolute_links)
