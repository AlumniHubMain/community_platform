# Copyright 2024 Alumnihub

"""Base class for link extractors."""

from abc import ABC, abstractmethod

from loguru import logger
from playwright.async_api import Browser, Page, Playwright, async_playwright


class BaseLinkExtractor(ABC):
    """Base class for link extractors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the extractor."""

    def __init__(self, base_url: str, logger: logger = logger) -> None:
        """Initialize the link extractor."""
        self.base_url = base_url
        self.timeout = 60000  # 60 seconds
        self.logger = logger.bind(base_url=base_url)
        self.browser_args = [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-background-timer-throttling",
            "--disable-popup-blocking",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-window-activation",
            "--disable-focus-on-load",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-startup-window",
            "--window-position=0,0",
            "--window-size=1280,1000",
            "--disable-web-security",
            "--disable-site-isolation-trials",
            "--disable-features=IsolateOrigins,site-per-process",
        ]
        self.logger.info("Initialized link extractor for {base_url}", base_url=self.base_url)

    async def _init_browser(self) -> tuple[Playwright, Browser, Page]:
        """Initialize the browser and page.

        Returns:
            tuple[Playwright, Browser, Page]: Initialized playwright, browser and page instances

        """
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True, args=self.browser_args)
        page = await browser.new_page()
        try:
            await page.goto(self.base_url)
        except Exception as e:  # noqa: BLE001
            self.logger.info("Error while navigating to {base_url}: {error}", base_url=self.base_url, error=e)
        return playwright, browser, page

    @abstractmethod
    async def _load_all_content(self, page: Page) -> None:
        """Load all content on the page."""

    @abstractmethod
    async def _extract_links(self, page: Page) -> list[str]:
        """Extract links from the page."""

    async def get_links(self) -> list[str]:
        """Extract links from the target URL.

        Returns:
            List of vacancy links.

        """
        playwright, browser, page = await self._init_browser()
        await self._load_all_content(page)
        links = await self._extract_links(page)
        await browser.close()
        await playwright.stop()
        return links
