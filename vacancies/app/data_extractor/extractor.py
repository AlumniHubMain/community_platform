# Copyright 2024 Alumnihub
"""Extractor of vacancy data."""

import asyncio

from langchain_google_vertexai import ChatVertexAI
from loguru import logger
from playwright.async_api import async_playwright

from app.data_extractor.structure_vacancy import Vacancy


class VacancyExtractor:
    """Handles parallel extraction of vacancy data using multiple browser instances and LLM."""

    def __init__(self, max_concurrent_browsers: int = 3, logger: logger = logger) -> None:
        """Initialize the VacancyExtractor."""
        self.max_concurrent_browsers = max_concurrent_browsers
        self.browser_semaphore = asyncio.Semaphore(max_concurrent_browsers)
        self.llm = self._initialize_llm()
        self.structured_llm = self.llm.with_structured_output(Vacancy)
        self.playwright = None
        self.browser = None
        self.logger = logger

    async def __aenter__(self) -> "VacancyExtractor":
        """Initialize browser on context manager enter.

        Returns:
            VacancyExtractor: Initialized VacancyExtractor

        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
            ],
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        """Clean up browser resources on context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _initialize_llm(self) -> ChatVertexAI:  # noqa: PLR6301
        """Initialize the LLM model.

        Returns:
            ChatVertexAI: Initialized LLM model

        """
        return ChatVertexAI(
            model="gemini-1.5-flash-002",
            temperature=0,
            max_tokens=None,
            max_retries=6,
            stop=None,
        )

    async def _extract_html(self, url: str) -> str:
        """Extract HTML content from a vacancy page.

        Args:
            url (str): URL of the vacancy page


        Returns:
            str: HTML content of the page

        """
        async with self.browser_semaphore:
            page = await self.browser.new_page()
            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle")
            except Exception as e:  # noqa: BLE001
                self.logger.warning("Error loading page {url}: {error}", url=url, error=e)
            return await page.content()

    async def process_vacancy(self, url: str) -> Vacancy | None:
        """Process a single vacancy URL to extract structured data.

        Args:
            url (str): URL of the vacancy page

        Returns:
            Vacancy | None: Structured vacancy data or None if extraction failed

        """
        try:
            html_content = await self._extract_html(url)
            if not html_content:
                return None

            return self.structured_llm.invoke(html_content)
        except Exception as e:
            self.logger.exception("Error processing vacancy {url}: {error}", url=url, error=e)
            return None

    async def process_vacancies(self, urls: list[str]) -> list[Vacancy]:
        """Process multiple vacancy URLs in parallel.

        Args:
            urls (List[str]): List of vacancy URLs to process

        Returns:
            List[Vacancy]: List of structured vacancy data

        """
        async with self as extractor:
            tasks = [extractor.process_vacancy(url) for url in urls]
            results = await asyncio.gather(*tasks)
            return [result for result in results if result is not None]
