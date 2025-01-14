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
        self._playwright = None
        self._browser = None
        self._page = None
        self.logger.info("Initialized link extractor for {base_url}", base_url=self.base_url)

    async def _init_browser(self) -> tuple[Playwright, Browser, Page]:
        """Initialize the browser and page.

        Returns:
            Playwright, Browser, Page: The initialized browser, page, and playwright.

        """
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True, args=self.browser_args)
        self._page = await self._browser.new_page()
        try:
            await self._page.goto(self.base_url)
        except Exception as e:  # noqa: BLE001
            self.logger.info("Error while navigating to {base_url}: {error}", base_url=self.base_url, error=e)
        return self._playwright, self._browser, self._page

    @abstractmethod
    async def _load_all_content(self, page: Page) -> None:
        """Load all content on the page."""

    @abstractmethod
    async def _extract_links(self, page: Page) -> list[str]:
        """Extract links from the page."""

    async def close(self) -> None:
        """Close all resources."""
        if self._page:
            await self._page.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        # Add any additional cleanup needed by child classes
        await self._cleanup()

    @abstractmethod
    async def _cleanup(self) -> None:
        """Additional cleanup for child classes to implement."""

    async def get_links(self) -> list[str]:
        """Extract links from the target URL.

        Returns:
            List of vacancy links.

        """
        try:
            await self._init_browser()
            await self._load_all_content(self._page)
            return await self._extract_links(self._page)
        finally:
            await self.close()
