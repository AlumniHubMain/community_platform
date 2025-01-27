from typing import Dict, Any
from linkedin_api import Linkedin
from linkedin_api.client import ChallengeException, UnauthorizedException
from loguru import logger

from src.linkedin.base import LinkedInRepository
from config import settings
from src.exceptions import (
    LinkedInAuthError, LinkedInBlockedError, 
    LinkedInSessionError, TomQuirkAPIError
)
from src.db.models.limits import LinkedInProviderType


class LinkedInTomquirkRepository(LinkedInRepository):
    """Implementation using TomQuirk's linkedin-api"""
    
    def __init__(self):
        self.provider_id = LinkedInProviderType.TOMQUIRK
        
    @classmethod
    def _get_api(cls) -> Linkedin:
        """Lazy initialization of API client"""
        return Linkedin(
            settings.linkedin_email.get_secret_value(),
            settings.linkedin_password.get_secret_value()
        )
    
    @classmethod
    async def get_profile(cls, username: str, use_mock: bool = False) -> Dict[str, Any]:
        try:
            api = cls._get_api()
            return api.get_profile(username)
            
        except UnauthorizedException as e:
            raise LinkedInAuthError("LinkedIn authentication failed")
        except ChallengeException as e:
            raise LinkedInBlockedError("LinkedIn blocked the request")
        except Exception as e:
            if "session" in str(e).lower():
                raise LinkedInSessionError("LinkedIn session expired")
            raise TomQuirkAPIError(f"LinkedIn API error: {e}")
