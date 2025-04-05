# Copyright 2024 Alumnihub
"""Extractor of vacancy data."""

import traceback

from langchain_google_vertexai import ChatVertexAI
from langchain_google_vertexai.callbacks import VertexAICallbackHandler
from picologging import Logger
from playwright.async_api import async_playwright

from app.core.data_extractor.structure_vacancy import VacancyStructure


class VacancyExtractor:
    """Handles extraction of vacancy data using browser instance and LLM."""

    def __init__(
        self,
        max_input_tokens: int = 100_000_000,
        max_output_tokens: int = 100_000_000,
        logger: Logger = Logger,
    ) -> None:
        """Initialize the VacancyExtractor with LLM model.

        Args:
            max_input_tokens: Maximum number of input tokens to use
            max_output_tokens: Maximum number of output tokens to use
            logger: Logger instance
            monitoring: Monitoring instance
        """
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens
        self.logger = logger
        self.llm = ChatVertexAI(
            model="gemini-1.5-flash-002", temperature=0, max_retries=6, convert_system_message_to_human=True
        )
        self.structured_llm = self.llm.with_structured_output(VacancyStructure)
        self.vertex_callback = VertexAICallbackHandler()

    def __name__(self) -> str:
        """Get the name of the extractor."""
        return "data_extractor"

    async def process_vacancy(self, url: str) -> VacancyStructure | None:
        """Process a vacancy URL to extract structured data.

        Args:
            url (str): URL of the vacancy page

        Returns:
            VacancyStructure | None: Structured vacancy data or None if extraction failed
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                try:
                    await page.goto(url, timeout=30000)
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_selector(".loading-spinner", state="hidden", timeout=10000)
                except Exception:
                    self.logger.warning(
                        {
                            "message": "Error loading page",
                            "url": url,
                            "error": traceback.format_exc(),
                            "extractor_name": self.name,
                        },
                    )
                    await browser.close()
                    return None

                html = await page.evaluate("""
                    () => {
                        // Try different selectors for the main content
                        const selectors = [
                            '.vacancy-description',  // Common class for vacancy content
                            'main',                 // Main content area
                            'article',              // Article content
                            '#content'              // Content div
                        ];
                        
                        for (const selector of selectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                return element.innerText;
                            }
                        }
                        
                        // Fallback: return body text if no specific container found
                        return document.body.innerText;
                    }
                """)

                if not html:
                    self.logger.warning(
                        {
                            "message": "No vacancy content found",
                            "url": url,
                            "extractor_name": self.name,
                        },
                    )
                    await browser.close()
                    return None

                # Process with LLM
                prompt = f"Extract job vacancy information from the following text:\n\n{html}"
                vacancy = self.structured_llm.invoke(prompt, config={"callbacks": [self.vertex_callback]})
                prompt_tokens = self.vertex_callback.prompt_tokens
                completion_tokens = self.vertex_callback.completion_tokens

                # Track token usage
                self.max_input_tokens -= prompt_tokens
                self.max_output_tokens -= completion_tokens

                # Record token usage in monitoring if available

                self.logger.info(
                    {
                        "message": "Token usage stats",
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                        "extractor_name": self.name,
                    },
                )

                await browser.close()
                return vacancy

        except Exception:
            self.logger.exception(
                {
                    "message": "Error processing vacancy",
                    "url": url,
                    "error": traceback.format_exc(),
                    "extractor_name": self.name,
                },
            )
            return None

    def get_current_tokens(self) -> tuple[int, int]:
        """Get the current number of tokens for the input text."""
        return self.max_input_tokens, self.max_output_tokens
