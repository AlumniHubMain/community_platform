from loguru import logger
from playwright.async_api import Page

from app.link_extractor.base import BaseLinkExtractor


class JetBrainsLinkExtractor(BaseLinkExtractor):
    def __init__(self, logger: logger = logger) -> None:
        super().__init__("https://www.jetbrains.com/careers/jobs/", logger)

    @property
    def name(self) -> str:
        return "JetBrains"

    async def _load_all_content(self, page: Page) -> None:
        try:
            # Wait for the initial vacancy links to load
            await page.wait_for_selector('a[href^="/careers/jobs/"]', timeout=self.timeout)
        except TimeoutError as e:
            self.logger.info("Timeout while loading content", error=e)
            return  # Exit early if the initial content doesn't load

        # Extract all links from the JavaScript variable VACANCIES
        all_links = await page.evaluate("() => VACANCIES.map(v => v.slug)")
        self.all_links = set(f"/careers/jobs/{link}" for link in all_links)  # Construct full URLs

        self.logger.info(
            "Found all vacancies",
            total_links=len(self.all_links),
        )

    async def _extract_links(self, page: Page) -> list[str]:
        return list(getattr(self, "all_links", set()))
