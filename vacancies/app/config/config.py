# Copyright 2024 Alumnihub

"""Configuration for the application."""

import json
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.link_extractor import BaseLinkExtractor, BookingLinkExtractor


class Credentials(BaseSettings):
    """Class for storing credentials."""

    DB_NAME: str
    DB_USER: str
    DB_PASS: str

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True)

    @classmethod
    def load(cls) -> "Credentials":
        """Load credentials from environment variable.

        Returns:
            Credentials: Instance of Credentials class with loaded values.

        """
        secret = os.environ.get("BACKEND_CREDENTIALS")
        if secret:
            creds_dict = json.loads(secret)
            for key, value in creds_dict.items():
                os.environ[key] = value
        return cls()


class Config(BaseSettings):
    """Application settings."""

    CONCURRENT_EXTRACTIONS: int = 3

    # Dictionary mapping company names to their extractor classes
    EXTRACTORS: dict[str, type[BaseLinkExtractor]] = {
        "booking": BookingLinkExtractor,
    }


config = Config()
credentials = Credentials.load()
