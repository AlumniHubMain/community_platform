import aiohttp
from loguru import logger
from typing import Dict, Any, List

from ..base import LinkedInRepository
from .mock_data import MOCK_PROFILE_RESPONSE
from config import settings

from src.exceptions import (
    CredentialsError, ProfileNotFoundError, RateLimitError, ScrapinAPIError,
    BadRequestError, PaymentRequiredError, ForbiddenError, ServerError
)

from common_db.models.linkedin_helpers import LinkedInProvider


class LinkedInScrapinRepository(LinkedInRepository):
    """Implementation using Scrapin.io API"""

    BASE_URL = "https://api.scrapin.io/enrichment/profile"

    def __init__(self, use_mock: bool = False):
        self.provider_id = LinkedInProvider.SCRAPIN

    @classmethod
    async def _make_request(cls, linkedin_url: str) -> Dict[str, Any]:
        """Выполняет запрос к Scrapin.io API"""
        try:
            params = {
                "apikey": settings.scrapin_api_key.get_secret_value(),
                "linkedInUrl": linkedin_url
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(cls.BASE_URL, params=params) as response:
                    if response.status == 400:
                        raise BadRequestError("Missing or invalid parameters")

                    if response.status == 401:
                        raise CredentialsError("Invalid API token")

                    if response.status == 402:
                        raise PaymentRequiredError("Insufficient credits")

                    if response.status == 403:
                        raise ForbiddenError("API key lacks permissions")

                    if response.status == 404:
                        raise ProfileNotFoundError(f"No results found for: {linkedin_url}")

                    if response.status == 429:
                        raise RateLimitError("Rate limit exceeded (500 requests/minute)")

                    if response.status == 500:
                        raise ServerError("ScrapIn API server error")

                    if response.status > 500:
                        raise ScrapinAPIError(
                            f"Unexpected API error: {await response.text()}",
                            status_code=response.status
                        )

                    return await response.json()

        except aiohttp.ClientError as e:
            raise ScrapinAPIError(f"Network error: {e}")

    @classmethod
    async def get_profile(cls, username: str, use_mock: bool = False) -> Dict[str, Any]:
        """Get LinkedIn profile data by username"""
        if use_mock:
            return MOCK_PROFILE_RESPONSE

        linkedin_url = f"https://www.linkedin.com/in/{username}/"
        return await cls._make_request(linkedin_url)

    @classmethod
    async def get_connections(cls, username: str) -> List[Dict[str, Any]]:
        logger.warning("Scrapin.io API doesn't support getting connections")
        return []
