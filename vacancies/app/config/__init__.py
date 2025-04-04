# Copyright 2024 Alumnihub

"""Configuration for the application."""

from .config import config, credentials
from .logger import setup_logging
from .monitoring import VacanciesMonitoring

__all__ = ["config", "credentials", "setup_logging", "VacanciesMonitoring"]
