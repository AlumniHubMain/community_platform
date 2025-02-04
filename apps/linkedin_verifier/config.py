from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Dict
from google.oauth2 import service_account
from loguru import logger

from common_db.models.linkedin_helpers import LinkedInProvider


class Settings(BaseSettings):
    """Application settings"""
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LinkedIn API Service"

    # Database
    db_host: SecretStr
    db_port: int
    db_name: SecretStr
    db_user: SecretStr
    db_pass: SecretStr
    
    # Scrapin.io settings
    scrapin_api_key: SecretStr | None = None
    
    # Google Cloud
    google_cloud_project: str
    google_application_credentials: str
    
    # Topics
    linkedin_tasks_topic: str = "linkedin-tasks"
    linkedin_limits_topic: str = "linkedin-limits"

    # LinkedIn Provider
    linkedin_provider: LinkedInProvider = LinkedInProvider.SCRAPIN
    linkedin_email: SecretStr | None = None  # для TomQuirk
    linkedin_password: SecretStr | None = None  # для TomQuirk

    # NATS settings
    nats_url: str = "nats://localhost:4222"
    linkedin_tasks_stream: str = "linkedin_tasks_stream"
    
    # Message Broker Provider
    message_broker: str = "google"  # или "nats"

    # Google Cloud PubSub
    google_project_id: str
    google_credentials_path: str
    
    # PubSub Topics & Subscriptions
    pubsub_linkedin_tasks_topic: str = "linkedin-tasks"
    pubsub_linkedin_tasks_sub: str = "linkedin-tasks-sub"
    pubsub_limits_alert_topic: str = "linkedin-limits"
    pubsub_limits_alert_sub: str = "linkedin-limits-sub"
    
    @property
    def google_credentials(self) -> service_account.Credentials:
        """Get Google credentials from JSON file"""
        return service_account.Credentials.from_service_account_file(
            self.google_credentials_path
        )

    @property
    def database_url_asyncpg(self) -> SecretStr:
        return SecretStr(
            f"postgresql+asyncpg://"
            f"{self.db_user.get_secret_value()}:"
            f"{self.db_pass.get_secret_value()}@"
            f"{self.db_host.get_secret_value()}:"
            f"{self.db_port}/"
            f"{self.db_name.get_secret_value()}"
        )

    @property
    def api_keys(self) -> Dict[LinkedInProvider, SecretStr]:
        """Маппинг provider_id -> api_key с использованием SecretStr"""
        return {
            LinkedInProvider.SCRAPIN: self.scrapin_api_key,
            LinkedInProvider.TOMQUIRK: self.linkedin_password
        }

    @property
    def current_provider(self) -> LinkedInProvider:
        """Текущий провайдер из конфига"""
        return self.linkedin_provider

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )


# Создаем и валидируем настройки при импорте
settings = Settings()

# Настройка логирования
logger.add(
    Path("logs/app.log"),
    rotation="1 day",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)
