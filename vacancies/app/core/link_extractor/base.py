# Copyright 2024 Alumnihub

"""Base class for link extractors."""

import traceback
from abc import ABC, abstractmethod

from picologging import Logger
from playwright.async_api import Browser, Page, Playwright, async_playwright


class BaseLinkExtractor(ABC):
    """Base class for link extractors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the extractor."""

    def __init__(self, base_url: str, logger: Logger = Logger) -> None:
        """Initialize the link extractor."""
        self.base_url = base_url
        self.timeout = 60000  # 60 seconds
        self.logger = logger
        self.logger.info("Initializing link extractor", extra={"base_url": base_url})
        self.browser_args = [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-background-timer-throttling",
            "--disable-popup-blocking",
            "--disable-backgrounding-occluded-windows",
            "--disable-window-activation",
            "--disable-focus-on-load",
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

    async def _init_browser(self) -> tuple[Playwright, Browser, Page]:
        """Initialize the browser and page.

        Returns:
            Playwright, Browser, Page: The initialized browser, page, and playwright.

        """
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True, args=self.browser_args)
        self._page = await self._browser.new_page()
        await self._page.set_viewport_size({"width": 1280, "height": 800})
        await self._page.set_extra_http_headers({
            "Accept-Language": "en",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0",
        })
        try:
            await self._page.goto(self.base_url, timeout=self.timeout)
        except Exception:
            self.logger.error(
                {
                    "message": "Error while navigating",
                    "base_url": self.base_url,
                    "error": traceback.format_exc(),
                },
            )
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
