# Copyright 2024 Alumnihub

"""Configuration for the application."""

from .config import config, credentials
from .logger import logger_config
from .monitoring import VacanciesMonitoring

__all__ = ["config", "credentials", "logger_config", "VacanciesMonitoring"]
