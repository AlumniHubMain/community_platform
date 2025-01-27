from enum import Enum
from sqlalchemy import Enum as PGEnum


class LinkedInProvider(str, Enum):
    """Типы провайдеров LinkedIn"""
    SCRAPIN = "scrapin"
    TOMQUIRK = "tomquirk"


LinkedInProviderType = PGEnum(LinkedInProvider, name='linkedinprovidertype', inherit_schema=True)
