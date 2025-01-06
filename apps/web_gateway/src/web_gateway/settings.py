from pydantic import BaseModel

from config_library import BaseConfig, FieldType
from common_db.config import PgSettings


class GoogleS3Settings(BaseModel):
    bucket: str


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
    environment: FieldType[str] = '/config/environment'
    google_application_credentials: FieldType[str] = '/config/credentials'
    s3: FieldType[GoogleS3Settings] = '/config/s3.json'
    secret_files: FieldType[SecretFiles] = '/config/secret_files.json'
    emitter_settings: FieldType[EmitterSettings] = '/config/emitter_settings.json'
    limits: FieldType[LimitsSettings] = '/config/limits.json'


settings = Settings()
