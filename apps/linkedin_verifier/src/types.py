from enum import Enum


class LinkedInProviderType(str, Enum):
    """Типы провайдеров LinkedIn"""
    SCRAPIN = "scrapin"
    TOMQUIRK = "tomquirk"
