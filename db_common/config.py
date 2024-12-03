import os
from typing import Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    db_host: SecretStr
    db_port: int
    db_name: SecretStr
    db_user: SecretStr
    db_pass: SecretStr
    db_schema: str = "alh_community_platform"
    
    # Google Cloud settings
    google_application_credentials: Optional[str] = None
    google_cloud_bucket: Optional[str] = None
    
    # Service-specific settings
    environment: str = "development"
    service_name: str  # Will be set by each service

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

    model_config = SettingsConfigDict(
        env_file=os.environ.get("DOTENV", ".env"),
        env_file_encoding="utf8"
    ) 
    
settings = DatabaseSettings()