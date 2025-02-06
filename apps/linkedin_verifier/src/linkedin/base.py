from abc import ABC, abstractmethod
from typing import Dict, Any, List


class LinkedInRepository(ABC):
    """Base class for LinkedIn data providers"""
    
    @classmethod
    @abstractmethod
    async def get_profile(cls, username: str, use_mock: bool = False) -> Dict[str, Any]:
        """Get LinkedIn profile data"""
        pass

    @classmethod
    @abstractmethod
    async def get_connections(cls, username: str) -> List[Dict[str, Any]]:
        """Get profile connections"""
        pass
