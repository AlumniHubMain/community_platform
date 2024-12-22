import json
import os

from alumnihub.community_platform.config_library import PlatformSettings, PlatformPGSettings

from pydantic_settings import SettingsConfigDict


class Settings(PlatformSettings):
    db_config: str
    google_application_credentials: str
    google_cloud_bucket: str
    environment: str
    bot_token_file: str
    access_secret_file: str
    google_pubsub_notification_topic: str
    notification_target: str = "pubsub"

    model_config = SettingsConfigDict(
        env_file=os.environ.get("DOTENV", ".env"), env_file_encoding="utf8"
    )


# При импорте файла сразу создастся и провалидируется объект конфига,
# который можно далее импортировать из разных мест
settings = Settings()