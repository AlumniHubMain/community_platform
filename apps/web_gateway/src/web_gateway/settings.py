from pydantic import BaseModel

from config_library import BaseConfig, FieldType


class SecretFiles(BaseModel):
    access_secret_file: str
    bot_token_file: str


class EmitterSettings(BaseModel):
    meetings_notification_target: str
    meetings_google_pubsub_notification_topic: str


class LimitsSettings(BaseModel):
    max_user_confirmed_meetings_count: int
    max_user_pended_meetings_count: int


class Settings(BaseConfig):
    # ToDo(und3v3l0p3d): Move db_config into root config
    environment: str = "dev"
    google_application_credentials: str = "./config/credentials.json"
    google_cloud_bucket: str = "community_platform_media1"
    emitter_settings: FieldType[EmitterSettings] = "./public_config/emitter_settings.json"
    limits: FieldType[LimitsSettings] = "./public_config/limits.json"
    secret_files: FieldType[SecretFiles] = "./config/secret_files.json"


settings = Settings()
