from abc import ABC, abstractmethod


class LinkedInRepository(ABC):
    """Base class for LinkedIn data providers"""
    
    @classmethod
    @abstractmethod
    async def get_profile(cls, username: str, use_mock: bool = False) -> dict:
        """Get LinkedIn profile data"""
        pass

    @classmethod
    @abstractmethod
    async def get_connections(cls, username: str) -> list[dict]:
        """Get profile connections"""
        pass