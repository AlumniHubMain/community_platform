import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: SecretStr
    db_port: int
    db_name: SecretStr
    db_user: SecretStr
    db_pass: SecretStr
    db_schema: str  # DB_SCHEMA=your_schema (default=public)
    google_application_credentials: str
    google_cloud_bucket: str

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

    model_config = SettingsConfigDict(env_file=os.environ.get("DOTENV", ".env"), env_file_encoding="utf8")


# При импорте файла сразу создастся и провалидируется объект конфига,
# который можно далее импортировать из разных мест
settings = Settings()
