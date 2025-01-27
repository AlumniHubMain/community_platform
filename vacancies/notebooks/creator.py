import argparse
import asyncio
from typing import Optional

from langchain_core.prompts import PromptTemplate
from langchain_google_vertexai import ChatVertexAI
from loguru import logger
from playwright.async_api import async_playwright


class VacancyExtractorGenerator:
    """Generator for vacancy extractor classes based on webpage analysis."""

    def __init__(self) -> None:
        self.llm = ChatVertexAI(
            model="gemini-1.5-pro-002",
            temperature=0,
            max_tokens=None,
            max_retries=6,
            stop=None,
        )

        self.prompt = PromptTemplate(
            input_variables=["html_content"],
            template="""
            analyze the following html content and write a python class for extracting links vacancies from this page
            
            this is example of class:
            import traceback

            from loguru import logger
            from playwright.async_api import Page

            from app.link_extractor.base import BaseLinkExtractor


            class BookingLinkExtractor(BaseLinkExtractor):

                def __init__(self, logger: logger = logger) -> None:
                    super().__init__("https://jobs.booking.com/booking/jobs", logger)
                    self.all_links = set()

                @property
                def name(self) -> str:
                    return "Booking"

                async def _load_all_content(self, page: Page) -> None:
                    try:
                        await page.wait_for_selector('a[href*="/booking/jobs/"]', timeout=self.timeout)
                    except TimeoutError as e:
                        self.logger.info("Timeout while loading content", error=e)

                    while True:
                        current_links = await page.eval_on_selector_all(
                            'a[href*="/booking/jobs/"]',
                            "elements => elements.map(el => el.getAttribute('href'))",
                        )
                        self.all_links.update(current_links)
                        self.logger.info(
                            "Found vacancies on current page",
                            current_links=len(current_links),
                            total_links=len(self.all_links),
                        )

                        try:
                            next_button = await page.query_selector(
                                "button.mat-focus-indicator.mat-tooltip-trigger"
                                ".mat-paginator-navigation-next.mat-icon-button"
                                ".mat-button-base",
                            )

                            if not next_button or await next_button.is_disabled():
                                self.logger.info("No more links on the pages available")
                                break

                            await next_button.click()
                            await page.wait_for_load_state("networkidle")
                            await page.wait_for_timeout(2000)
                        except Exception:  # noqa: BLE001
                            self.logger.info("Error during pagination", error=traceback.format_exc())
                            break

                async def _extract_links(self, page: Page) -> list[str]:  # noqa: ARG002
                    return list(getattr(self, "all_links", set()))

            {html_content}
            """,
        )

    async def get_page_content(self, url: str) -> Optional[str]:
        """Fetch HTML content from the given URL."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_load_state("networkidle")
                await page.wait_for_selector(".loading-spinner", state="hidden", timeout=10000)
                return await page.content()
            except Exception as e:
                logger.error(f"Error fetching page content: {e}")
                return None
            finally:
                await browser.close()

    async def generate_extractor(self, url: str) -> Optional[str]:
        """Generate vacancy extractor class for the given URL."""
        html_content = await self.get_page_content(url)
        if not html_content:
            return None

        llm_with_prompt = self.prompt | self.llm
        result = llm_with_prompt.invoke({"html_content": html_content})
        return result.content


async def main():
    parser = argparse.ArgumentParser(description="Generate vacancy extractor class for a website")
    parser.add_argument("url", type=str, help="URL of the vacancy page to analyze")
    parser.add_argument("--output", type=str, default="result.py", help="Output file path (default: result.py)")
    args = parser.parse_args()

    generator = VacancyExtractorGenerator()
    result = await generator.generate_extractor(args.url)

    if result:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            logger.info(f"Successfully generated extractor class and saved to {args.output}")
        except Exception as e:
            logger.error(f"Failed to save result to file: {e}")
    else:
        logger.error("Failed to generate extractor class")


if __name__ == "__main__":
    asyncio.run(main())
