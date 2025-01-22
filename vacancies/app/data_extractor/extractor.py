# Copyright 2024 Alumnihub
"""Extractor of vacancy data."""

import httpx
from langchain_google_vertexai import ChatVertexAI
from langchain_google_vertexai.callbacks import VertexAICallbackHandler
from loguru import logger

from app.data_extractor.structure_vacancy import VacancyStructure


class VacancyExtractor:
    """Handles extraction of vacancy data using browser instance and LLM."""

    def __init__(self, logger: logger = logger) -> None:
        """Initialize the VacancyExtractor with LLM model.

        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.llm = ChatVertexAI(
            model="gemini-1.5-flash-002",
            temperature=0,
            max_retries=6,
        )
        self.structured_llm = self.llm.with_structured_output(VacancyStructure)
        self.vertex_callback = VertexAICallbackHandler()

    async def process_vacancy(self, url: str) -> VacancyStructure | None:
        """Process a vacancy URL to extract structured data.

        Args:
            url (str): URL of the vacancy page

        Returns:
            VacancyStructure | None: Structured vacancy data or None if extraction failed
        """
        try:
            response = httpx.get(url)

            if response.status_code == 200:
                html = response.text
            else:
                self.logger.error(f"Failed to fetch URL {url}: {response.status_code}")
                return None

            # Process with LLM
            vacancy = self.structured_llm.invoke(html, config={"callbacks": [self.vertex_callback]})
            if vacancy:
                return vacancy

        except Exception as e:
            self.logger.exception("Error processing vacancy {url}: {error}", url=url, error=e)
            return None
